"""
Training pipeline for all three TPS ML models.

Generates synthetic telemetry from the physics equations, trains
scikit-learn models, and writes .pkl artifacts to ml/models/.

Run from project root:
    python ml/training/train_heat_predictor.py

Requirements:
    pip install scikit-learn numpy joblib
"""

import math
import os
import json
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, roc_auc_score

# ---------------------------------------------------------------------------
# Synthetic data generator — mirrors the real physics modules exactly
# ---------------------------------------------------------------------------
MATERIALS = {
    "c_phenolic":               {"max_temp_k": 2200, "conductivity_w_mk": 0.7,  "density_kg_m3": 1450, "sustainability": 0.55},
    "reinforced_carbon_carbon": {"max_temp_k": 2700, "conductivity_w_mk": 4.5,  "density_kg_m3": 1800, "sustainability": 0.62},
    "ultra_high_temp_ceramic":  {"max_temp_k": 3200, "conductivity_w_mk": 18.0, "density_kg_m3": 5600, "sustainability": 0.48},
    "bio_ceramic_composite":    {"max_temp_k": 1900, "conductivity_w_mk": 1.4,  "density_kg_m3": 1320, "sustainability": 0.86},
}

def iso_density(altitude_m: float) -> float:
    """ISO 2533 single-pass density (matches aerodynamics module)."""
    layers = [
        (0,     288.15, -0.0065),
        (11000, 216.65,  0.0),
        (20000, 216.65,  0.001),
        (32000, 228.65,  0.0028),
        (47000, 270.65,  0.0),
        (51000, 270.65, -0.0028),
        (71000, 214.65, -0.002),
        (86000, 186.87,  0.0),
    ]
    g0, R = 9.80665, 287.058
    T, P  = 288.15, 101325.0
    h     = min(max(altitude_m, 0.0), 86000.0)
    for i, (h_base, T_base, lapse) in enumerate(layers):
        h_top = layers[i + 1][0] if i + 1 < len(layers) else 86000.0
        if h <= h_top:
            dh = h - h_base
            if abs(lapse) < 1e-10:
                T = T_base
                P *= math.exp(-g0 * dh / (R * T_base))
            else:
                T = T_base + lapse * dh
                P *= (T / T_base) ** (-g0 / (lapse * R))
            break
        else:
            dh = h_top - h_base
            if abs(lapse) < 1e-10:
                T_next = T_base
                P *= math.exp(-g0 * dh / (R * T_base))
            else:
                T_next = T_base + lapse * dh
                P *= (T_next / T_base) ** (-g0 / (lapse * R))
            T = T_next
    return P / (R * T)

def fay_riddell(rho, velocity, nose_radius):
    return 1.83e-4 * math.sqrt(max(rho, 1e-6) / max(nose_radius, 0.01)) * velocity ** 3

def wall_temp(net_flux, thickness_mm, conductivity):
    return 350.0 + net_flux * ((thickness_mm / 1000.0) / max(conductivity, 0.1))

def generate_dataset(n_samples: int = 12_000) -> dict:
    rng = np.random.default_rng(42)
    mat_ids = list(MATERIALS.keys())

    rows = []
    for _ in range(n_samples):
        mach        = rng.uniform(4.0, 12.0)
        altitude_m  = rng.uniform(18_000, 60_000)
        aoa_deg     = rng.uniform(0.0, 10.0)
        nose_radius = rng.uniform(0.15, 0.6)
        thickness_mm = rng.uniform(20.0, 80.0)
        mass_flow   = rng.uniform(0.2, 2.0)
        surface_area = rng.uniform(30.0, 80.0)
        mat_id      = rng.choice(mat_ids)
        mat         = MATERIALS[mat_id]

        rho   = iso_density(altitude_m)
        gamma, R = 1.4, 287.058
        T_static  = 288.15 - 0.0065 * min(altitude_m, 11000)   # approx troposphere T
        a         = math.sqrt(gamma * R * max(T_static, 180))
        vel       = mach * a

        q_stag    = fay_riddell(rho, vel, nose_radius)
        aoa_rad   = math.radians(abs(aoa_deg))
        q         = q_stag * (1.0 + 0.5 * math.sin(aoa_rad) ** 2)

        cp        = 14300.0
        delta_t_k = 120.0
        q_removed = mass_flow * cp * delta_t_k / surface_area
        eff       = max(0.0, min(0.85, q_removed / max(q, 1.0)))
        q_net     = q * (1.0 - eff)

        T_wall    = wall_temp(q_net, thickness_mm, mat["conductivity_w_mk"])
        T_stag    = T_static * (1.0 + 0.5 * (gamma - 1) * mach ** 2)
        T_wall    = min(T_wall, T_stag)

        margin    = max(0.0, (mat["max_temp_k"] - T_wall) / mat["max_temp_k"])
        dyn_press = 0.5 * rho * vel ** 2

        rows.append({
            # features
            "mach":               mach,
            "altitude_m":         altitude_m,
            "density_kg_m3":      rho,
            "velocity_m_s":       vel,
            "dynamic_pressure_pa": dyn_press,
            "heat_flux_w_m2":     q,
            "net_heat_flux_w_m2": q_net,
            "cooling_efficiency": eff,
            "thickness_mm":       thickness_mm,
            "nose_radius_m":      nose_radius,
            "aoa_deg":            aoa_deg,
            "mat_max_temp_k":     mat["max_temp_k"],
            "mat_conductivity":   mat["conductivity_w_mk"],
            "mat_density":        mat["density_kg_m3"],
            "mat_sustainability": mat["sustainability"],
            # targets
            "wall_temp_k":        T_wall,
            "thermal_margin":     margin,
            "failure":            int(margin < 0.08),
            "mat_id":             mat_id,
        })
    return rows


# ---------------------------------------------------------------------------
# Model 1 — Heat predictor (wall temperature regression)
# ---------------------------------------------------------------------------
def train_heat_predictor(rows, out_dir):
    FEATURES = [
        "mach", "altitude_m", "density_kg_m3", "heat_flux_w_m2",
        "net_heat_flux_w_m2", "cooling_efficiency", "thickness_mm",
        "mat_conductivity", "nose_radius_m",
    ]
    X = np.array([[r[f] for f in FEATURES] for r in rows])
    y = np.array([r["wall_temp_k"] for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr", GradientBoostingRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            subsample=0.8, min_samples_leaf=10, random_state=42,
        )),
    ])
    model.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"  heat_predictor   MAE = {mae:.1f} K")

    os.makedirs(out_dir, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, os.path.join(out_dir, "model.pkl"))
    _write_model_card(out_dir, "heat_predictor", "GradientBoostingRegressor",
                      FEATURES, "wall_temp_k", f"MAE {mae:.1f} K on 15% holdout")


# ---------------------------------------------------------------------------
# Model 2 — Failure predictor (binary classifier)
# ---------------------------------------------------------------------------
def train_failure_predictor(rows, out_dir):
    FEATURES = [
        "thermal_margin", "dynamic_pressure_pa", "heat_flux_w_m2",
        "net_heat_flux_w_m2", "cooling_efficiency", "mach", "altitude_m",
    ]
    X = np.array([[r[f] for f in FEATURES] for r in rows])
    y = np.array([r["failure"] for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15,
                                                         random_state=42, stratify=y)
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("gbc", GradientBoostingClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.08,
            subsample=0.8, min_samples_leaf=8, random_state=42,
        )),
    ])
    model.fit(X_train, y_train)
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"  failure_predictor AUC = {auc:.3f}")

    os.makedirs(out_dir, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, os.path.join(out_dir, "model.pkl"))
    _write_model_card(out_dir, "failure_predictor", "GradientBoostingClassifier",
                      FEATURES, "failure (margin<0.08)", f"AUC {auc:.3f} on 15% holdout")


# ---------------------------------------------------------------------------
# Model 3 — Material recommender (ranking via predicted margin)
# ---------------------------------------------------------------------------
def train_material_recommender(rows, out_dir):
    """
    For each (flight_condition, material) pair, predict the thermal margin.
    At inference, all four materials are scored for the current conditions
    and ranked by predicted margin, weighted with sustainability.
    """
    FEATURES = [
        "heat_flux_w_m2", "net_heat_flux_w_m2", "cooling_efficiency",
        "thickness_mm", "nose_radius_m", "aoa_deg",
        "mat_max_temp_k", "mat_conductivity", "mat_density", "mat_sustainability",
    ]
    X = np.array([[r[f] for f in FEATURES] for r in rows])
    y = np.array([r["thermal_margin"] for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr", GradientBoostingRegressor(
            n_estimators=250, max_depth=4, learning_rate=0.06,
            subsample=0.8, min_samples_leaf=8, random_state=42,
        )),
    ])
    model.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"  material_recommender MAE = {mae:.4f} (margin)")

    os.makedirs(out_dir, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, os.path.join(out_dir, "model.pkl"))
    _write_model_card(out_dir, "material_recommender", "GradientBoostingRegressor",
                      FEATURES, "thermal_margin", f"MAE {mae:.4f} on 15% holdout")


def _write_model_card(out_dir, model_id, algo, features, target, metric):
    card = f"""# Model card — {model_id}

Algorithm : {algo}
Target    : {target}
Metric    : {metric}
Features  : {', '.join(features)}
Data      : 12 000 synthetic samples from physics simulation
Stage     : trained-surrogate
"""
    with open(os.path.join(out_dir, "model_card.md"), "w") as f:
        f.write(card)


# ---------------------------------------------------------------------------
# Registry updater
# ---------------------------------------------------------------------------
def update_registry(base_dir):
    registry = {
        "models": [
            {
                "model_id": "heat_predictor",
                "version": "0.2.0",
                "stage": "trained-surrogate",
                "artifact": "ml/models/heat_predictor/v0.2/model.pkl",
                "features": ["mach", "altitude_m", "density_kg_m3", "heat_flux_w_m2",
                             "net_heat_flux_w_m2", "cooling_efficiency", "thickness_mm",
                             "mat_conductivity", "nose_radius_m"],
            },
            {
                "model_id": "failure_predictor",
                "version": "0.2.0",
                "stage": "trained-surrogate",
                "artifact": "ml/models/failure_predictor/v0.2/model.pkl",
                "features": ["thermal_margin", "dynamic_pressure_pa", "heat_flux_w_m2",
                             "net_heat_flux_w_m2", "cooling_efficiency", "mach", "altitude_m"],
            },
            {
                "model_id": "material_recommender",
                "version": "0.2.0",
                "stage": "trained-surrogate",
                "artifact": "ml/models/material_recommender/v0.2/model.pkl",
                "features": ["heat_flux_w_m2", "net_heat_flux_w_m2", "cooling_efficiency",
                             "thickness_mm", "nose_radius_m", "aoa_deg",
                             "mat_max_temp_k", "mat_conductivity", "mat_density", "mat_sustainability"],
            },
        ]
    }
    path = os.path.join(base_dir, "registry.json")
    with open(path, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"  registry updated → {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    base_models = "ml/models"
    print("Generating synthetic dataset (12 000 samples)…")
    rows = generate_dataset(12_000)
    print(f"  failure rate in dataset: {sum(r['failure'] for r in rows)/len(rows):.1%}")

    print("Training heat_predictor…")
    train_heat_predictor(rows, os.path.join(base_models, "heat_predictor", "v0.2"))

    print("Training failure_predictor…")
    train_failure_predictor(rows, os.path.join(base_models, "failure_predictor", "v0.2"))

    print("Training material_recommender…")
    train_material_recommender(rows, os.path.join(base_models, "material_recommender", "v0.2"))

    print("Updating registry…")
    update_registry(base_models)

    print("\nDone. Artifacts written to ml/models/*/v0.2/model.pkl")