"""
ML Inference Adapter — loads trained scikit-learn models from ml/models/.

Falls back to heuristic surrogates if artifacts are not found, so the
backend runs correctly both before and after training.

Model loading order:
    1. Locate artifacts relative to this file (works from any cwd).
    2. joblib.load() the {"model": pipeline, "features": [...]} dict.
    3. Build feature vectors from DigitalTwinState on every tick.
"""

import math
import os
import logging
from typing import Any

import joblib

from app.schemas.digital_twin import DigitalTwinState
from app.simulation.materials import MATERIALS

logger = logging.getLogger(__name__)

# Resolve artifact paths relative to this source file so imports work
# regardless of where uvicorn is launched from.
_HERE        = os.path.dirname(__file__)
_MODELS_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", "ml", "models"))


def _load(model_id: str, version: str = "v0.2") -> dict | None:
    path = os.path.join(_MODELS_ROOT, model_id, version, "model.pkl")
    if not os.path.exists(path):
        logger.warning("Model artifact not found: %s — using heuristic fallback", path)
        return None
    try:
        artifact = joblib.load(path)
        logger.info("Loaded %s/%s from %s", model_id, version, path)
        return artifact
    except Exception as exc:
        logger.error("Failed to load %s: %s — using heuristic fallback", path, exc)
        return None


class MLInferenceAdapter:
    name = "ml_inference_adapter"

    def __init__(self) -> None:
        self._heat      = _load("heat_predictor")
        self._failure   = _load("failure_predictor")
        self._recommender = _load("material_recommender")

    # ------------------------------------------------------------------
    # Main update — called every simulation tick by the engine
    # ------------------------------------------------------------------
    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        state.ai.material_recommendation = self._rank_materials(state)
        state.ai.failure_probability     = self._failure_probability(state)
        state.ai.anomaly_score           = self._anomaly_score(state)
        state.ai.heat_forecast_k         = self._heat_forecast(state)
        state.ai.model_stage = (
            "trained-surrogate"
            if any(m is not None for m in [self._heat, self._failure, self._recommender])
            else "demo-surrogate"
        )
        return state

    # ------------------------------------------------------------------
    # 1. Material recommender
    # ------------------------------------------------------------------
    def _rank_materials(self, state: DigitalTwinState) -> list[str]:
        ranked = self.recommend_materials(
            heat_flux_w_m2=state.thermal.heat_flux_w_m2,
            net_heat_flux_w_m2=state.thermal.net_heat_flux_w_m2,
            cooling_efficiency=state.cooling.efficiency,
            thickness_mm=state.tps.thickness_mm,
            nose_radius_m=state.vehicle.nose_radius_m,
            aoa_deg=state.aircraft.angle_of_attack_deg,
            sustainability_weight=0.35,
        )
        return [item["material_id"] for item in ranked[:3]]

    def recommend_materials(
        self,
        heat_flux_w_m2: float,
        net_heat_flux_w_m2: float = 0.0,
        cooling_efficiency: float = 0.0,
        thickness_mm: float = 42.0,
        nose_radius_m: float = 0.35,
        aoa_deg: float = 4.0,
        sustainability_weight: float = 0.35,
    ) -> list[dict]:
        results = []

        if self._recommender is not None:
            model    = self._recommender["model"]
            features = self._recommender["features"]
            for mat_id, mat in MATERIALS.items():
                row = {
                    "heat_flux_w_m2":     heat_flux_w_m2,
                    "net_heat_flux_w_m2": net_heat_flux_w_m2,
                    "cooling_efficiency": cooling_efficiency,
                    "thickness_mm":       thickness_mm,
                    "nose_radius_m":      nose_radius_m,
                    "aoa_deg":            aoa_deg,
                    "mat_max_temp_k":     mat["max_temp_k"],
                    "mat_conductivity":   mat["conductivity_w_mk"],
                    "mat_density":        mat["density_kg_m3"],
                    "mat_sustainability": mat["sustainability"],
                }
                X = [[row[f] for f in features]]
                predicted_margin = float(model.predict(X)[0])
                # Weighted final score: predicted margin + sustainability bonus
                score = 0.65 * predicted_margin + sustainability_weight * mat["sustainability"]
                results.append({
                    "material_id": mat_id,
                    "name":        mat["name"],
                    "score":       round(score, 3),
                    "predicted_margin": round(predicted_margin, 3),
                })
        else:
            # Heuristic fallback
            required_temp = 1300 + heat_flux_w_m2 * 0.00042
            for mat_id, mat in MATERIALS.items():
                margin       = max(0.0, (mat["max_temp_k"] - required_temp) / mat["max_temp_k"])
                mass_penalty = min(0.35, mat["density_kg_m3"] / 12000)
                score        = 0.55 * margin + sustainability_weight * mat["sustainability"] - mass_penalty
                results.append({"material_id": mat_id, "name": mat["name"],
                                 "score": round(score, 3)})

        return sorted(results, key=lambda x: x["score"], reverse=True)

    # ------------------------------------------------------------------
    # 2. Failure probability
    # ------------------------------------------------------------------
    def _failure_probability(self, state: DigitalTwinState) -> float:
        if self._failure is not None:
            model    = self._failure["model"]
            features = self._failure["features"]
            row = {
                "thermal_margin":      state.thermal.thermal_margin,
                "dynamic_pressure_pa": state.aerodynamic.dynamic_pressure_pa,
                "heat_flux_w_m2":      state.thermal.heat_flux_w_m2,
                "net_heat_flux_w_m2":  state.thermal.net_heat_flux_w_m2,
                "cooling_efficiency":  state.cooling.efficiency,
                "mach":                state.aircraft.mach,
                "altitude_m":          state.aircraft.altitude_m,
            }
            X    = [[row[f] for f in features]]
            prob = float(model.predict_proba(X)[0][1])
            return round(min(0.99, max(0.0, prob)), 3)

        # Heuristic fallback
        return round(min(0.98, state.risk.score * 0.85
                         + max(0, 0.1 - state.thermal.thermal_margin)), 3)

    # ------------------------------------------------------------------
    # 3. Anomaly score — z-score on key telemetry channels
    # ------------------------------------------------------------------
    def _anomaly_score(self, state: DigitalTwinState) -> float:
        """
        Computes a normalised anomaly score [0, 1] by comparing current
        values against expected operating envelopes derived from training data.

        Expected ranges (µ ± 3σ from the synthetic dataset):
            cooling_efficiency : 0.42 ± 0.22
            thermal_margin     : 0.35 ± 0.25
            heat_flux (MW/m²)  : 2.5  ± 1.8
        """
        q_mw      = state.thermal.heat_flux_w_m2 / 1_000_000.0

        z_cooling = abs(state.cooling.efficiency   - 0.42) / 0.22
        z_margin  = abs(state.thermal.thermal_margin - 0.35) / 0.25
        z_flux    = abs(q_mw - 2.5) / 1.8

        # RMS of z-scores, capped at 1
        rms = math.sqrt((z_cooling**2 + z_margin**2 + z_flux**2) / 3.0)
        return round(min(1.0, rms / 3.0), 3)   # /3 → score≈1 when all channels are 3σ out

    # ------------------------------------------------------------------
    # 4. Heat forecast — trained regressor stepping forward N ticks
    # ------------------------------------------------------------------
    def _heat_forecast(self, state: DigitalTwinState, steps: int = 6) -> list[float]:
        if self._heat is None:
            # Heuristic fallback
            return [
                round(state.thermal.max_surface_temp_k * (1 + 0.012 * i)
                      - state.cooling.efficiency * 8 * i, 1)
                for i in range(1, steps + 1)
            ]

        model    = self._heat["model"]
        features = self._heat["features"]

        # Step forward: Mach increases ~0.015/tick, altitude drops ~1.8 m/tick
        # (matches engine.tick() increments)
        forecast = []
        mach     = state.aircraft.mach
        alt      = state.aircraft.altitude_m
        q_net    = state.thermal.net_heat_flux_w_m2
        eff      = state.cooling.efficiency

        for i in range(1, steps + 1):
            mach += 0.015
            alt   = max(18_000, alt - 1.8)
            # Approximate density for the stepped altitude
            rho   = _approx_density(alt)
            gamma, R = 1.4, 287.058
            T_s   = max(180.0, 288.15 - 0.0065 * min(alt, 11_000))
            vel   = mach * math.sqrt(gamma * R * T_s)
            q_new = 1.83e-4 * math.sqrt(max(rho, 1e-6) / 0.35) * vel ** 3
            eff_i = min(0.85, eff * (1 + 0.002 * i))   # slight cooling drift
            q_net_i = q_new * (1.0 - eff_i)

            row = {
                "mach":               mach,
                "altitude_m":         alt,
                "density_kg_m3":      rho,
                "heat_flux_w_m2":     q_new,
                "net_heat_flux_w_m2": q_net_i,
                "cooling_efficiency": eff_i,
                "thickness_mm":       state.tps.thickness_mm,
                "mat_conductivity":   _mat_conductivity(state.tps.material_id),
                "nose_radius_m":      state.vehicle.nose_radius_m,
            }
            X = [[row[f] for f in features]]
            T_pred = float(model.predict(X)[0])
            forecast.append(round(T_pred, 1))

        return forecast


# ---------------------------------------------------------------------------
# Small helpers used only inside this module
# ---------------------------------------------------------------------------
def _approx_density(altitude_m: float) -> float:
    """Single-exponential approximation — good enough for short forecast horizon."""
    return 1.225 * math.exp(-altitude_m / 8500.0)

def _mat_conductivity(material_id: str) -> float:
    from app.simulation.materials import MATERIALS as _M
    return _M.get(material_id, _M["c_phenolic"])["conductivity_w_mk"]