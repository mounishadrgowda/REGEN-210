import math

from app.schemas.digital_twin import DigitalTwinState
from app.simulation.materials import MATERIALS


class MLInferenceAdapter:
    name = "ml_inference_adapter"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        ranked = self.recommend_materials(
            heat_flux_w_m2=state.thermal.heat_flux_w_m2,
            sustainability_weight=0.35,
        )
        failure_probability = self.predict_failure_probability(state)
        state.ai.material_recommendation = [item["material_id"] for item in ranked[:3]]
        state.ai.model_stage = "surrogate-ensemble-v0.4"
        state.ai.failure_probability = failure_probability
        state.ai.anomaly_score = self.detect_anomaly(state)
        state.ai.heat_forecast_k = self.forecast_temperature_sequence(state)
        state.ai.spatial_heatmap_k = self.spatial_heatmap(state, rows=8, cols=16)
        state.ai.maintenance_remaining_cycles = state.structural.remaining_life_cycles
        state.ai.model_confidence = round(max(0.42, min(0.92, 0.88 - state.ai.anomaly_score * 0.22 - abs(state.aircraft.mach - 7.2) * 0.015)), 3)
        state.ai.surrogate_notes = [
            "Temperature forecast uses a lightweight LSTM-style recurrent surrogate.",
            "Failure probability uses a Random-Forest-style weighted ensemble over thermal, pressure, stress, and fatigue features.",
            "Spatial heat map uses a Gaussian-process-inspired radial basis surrogate over vehicle surface zones.",
        ]
        return state

    def forecast_temperature_sequence(self, state: DigitalTwinState, horizon_s: int = 30) -> list[float]:
        points = []
        memory_temp = state.thermal.max_surface_temp_k
        net_heat_mw = state.thermal.net_heat_flux_w_m2 / 1_000_000.0
        cooling_gain = state.cooling.efficiency + state.zonal_cooling.balance_quality * 0.08
        for idx in range(1, 7):
            gate = 1.0 / (1.0 + math.exp(-0.9 * (idx - 3)))
            heat_drive = net_heat_mw * (9.5 + idx * 1.2) * gate
            cooling_drive = cooling_gain * (7.0 + idx * 1.6)
            fatigue_bias = state.structural.fatigue_damage * idx * 18.0
            memory_temp = memory_temp * 0.94 + (memory_temp + heat_drive - cooling_drive + fatigue_bias) * 0.06
            points.append(round(memory_temp, 1))
        return points

    def predict_failure_probability(self, state: DigitalTwinState) -> float:
        thermal_vote = max(0.0, 1.0 - state.thermal.thermal_margin)
        pressure_vote = min(1.0, state.aerodynamic.dynamic_pressure_pa / 145_000.0)
        stress_vote = min(1.0, state.structural.joint_stress_mpa / 720.0)
        fatigue_vote = min(1.0, state.structural.fatigue_damage * 4.5)
        ablation_vote = min(1.0, state.structural.ablation_depth_mm / 7.5)
        rf_score = (
            0.34 * thermal_vote
            + 0.19 * pressure_vote
            + 0.21 * stress_vote
            + 0.16 * fatigue_vote
            + 0.1 * ablation_vote
        )
        return round(min(0.98, max(0.0, rf_score)), 3)

    def detect_anomaly(self, state: DigitalTwinState) -> float:
        expected_cooling = min(0.78, state.cooling.mass_flow_kg_s * 0.32)
        cooling_residual = abs(state.cooling.efficiency - expected_cooling)
        heat_residual = max(0.0, state.thermal.net_heat_flux_w_m2 - state.thermal.heat_flux_w_m2 * 0.92) / max(state.thermal.heat_flux_w_m2, 1.0)
        stress_residual = min(1.0, state.structural.joint_stress_mpa / 780.0)
        return round(min(1.0, cooling_residual * 1.2 + heat_residual * 0.65 + stress_residual * 0.28), 3)

    def spatial_heatmap(self, state: DigitalTwinState, rows: int = 8, cols: int = 16) -> list[list[float]]:
        peak = max(state.thermal.max_surface_temp_k, 260.0)
        cooling_zone = state.zonal_cooling.active_zone
        map_rows = []
        for y in range(rows):
            row = []
            y_norm = y / max(rows - 1, 1)
            leading_edge = math.sin(y_norm * math.pi)
            for x in range(cols):
                x_norm = x / max(cols - 1, 1)
                nose_kernel = math.exp(-(x_norm * 4.8) ** 2)
                combustor_kernel = math.exp(-((x_norm - 0.72) / 0.16) ** 2) * 0.24
                wing_kernel = leading_edge * math.exp(-((x_norm - 0.42) / 0.32) ** 2) * 0.32
                cooling_relief = 0.1 if cooling_zone in {"nose", "leading_edges"} and x_norm < 0.55 else 0.03
                temp = peak * (0.42 + 0.38 * nose_kernel + wing_kernel + combustor_kernel - cooling_relief)
                row.append(round(max(240.0, temp), 1))
            map_rows.append(row)
        return map_rows

    def recommend_materials(self, heat_flux_w_m2: float, sustainability_weight: float = 0.3) -> list[dict]:
        required_temp = 1300 + heat_flux_w_m2 * 0.00042
        ranked = []
        for material_id, material in MATERIALS.items():
            temp_margin = max(0.0, (material["max_temp_k"] - required_temp) / material["max_temp_k"])
            mass_penalty = min(0.35, material["density_kg_m3"] / 12000)
            score = 0.55 * temp_margin + sustainability_weight * material["sustainability"] - mass_penalty
            ranked.append({"material_id": material_id, "name": material["name"], "score": round(score, 3)})
        return sorted(ranked, key=lambda item: item["score"], reverse=True)

    def generate_design(self, mission: dict | None = None) -> dict:
        mission = mission or {}
        vehicle = mission.get("vehicle", {})
        initial = mission.get("initial_conditions", {})
        tps = mission.get("tps", {})
        cooling = mission.get("cooling", {})

        mach = min(8.8, max(4.0, float(initial.get("mach", 6.8))))
        altitude_m = float(initial.get("altitude_m", 31_000))
        velocity_m_s = mach * 295.0
        density = 1.225 * math.exp(-altitude_m / 8500.0)
        baseline_nose_radius = max(float(vehicle.get("nose_radius_m", 0.35)), 0.05)
        baseline_area = max(float(vehicle.get("reference_area_m2", 22.0)), 1.0)
        baseline_heat = 3.95e-4 * math.sqrt(max(density, 0.00001) / baseline_nose_radius) * velocity_m_s**3
        baseline_heat *= 1.0 + abs(float(initial.get("angle_of_attack_deg", 4.0))) * 0.025

        candidates = [
            {
                "name": "REGEN-HX2 Ogival Delta Waverider",
                "nose_radius_m": 0.72,
                "leading_edge_radius_mm": 9.5,
                "wing_sweep_deg": 74,
                "compression_ramp_deg": 8.2,
                "reference_area_m2": 24.5,
                "drag_coefficient": 0.39,
                "material_id": "ultra_high_temp_ceramic",
                "coolant": "liquid_hydrogen",
                "coolant_mass_flow_kg_s": 1.35,
                "rpic_bias": 0.16,
                "plasma_bias": 0.1,
            },
            {
                "name": "REGEN-HX2 Serrated Leading-Edge Lifter",
                "nose_radius_m": 0.58,
                "leading_edge_radius_mm": 7.0,
                "wing_sweep_deg": 71,
                "compression_ramp_deg": 7.4,
                "reference_area_m2": 23.0,
                "drag_coefficient": 0.35,
                "material_id": "reinforced_carbon_carbon",
                "coolant": "liquid_hydrogen",
                "coolant_mass_flow_kg_s": 1.55,
                "rpic_bias": 0.19,
                "plasma_bias": 0.08,
            },
            {
                "name": "REGEN-HX2 Bio-Ceramic Low-Mass Cruiser",
                "nose_radius_m": 0.82,
                "leading_edge_radius_mm": 11.0,
                "wing_sweep_deg": 76,
                "compression_ramp_deg": 6.8,
                "reference_area_m2": 26.0,
                "drag_coefficient": 0.43,
                "material_id": "bio_ceramic_composite",
                "coolant": "methane",
                "coolant_mass_flow_kg_s": 1.8,
                "rpic_bias": 0.13,
                "plasma_bias": 0.12,
            },
        ]

        best: dict | None = None
        for candidate in candidates:
            material = MATERIALS[candidate["material_id"]]
            radius_factor = math.sqrt(baseline_nose_radius / candidate["nose_radius_m"])
            sweep_factor = max(0.58, 1.0 - (candidate["wing_sweep_deg"] - 60.0) * 0.012)
            edge_factor = max(0.62, 1.0 - candidate["leading_edge_radius_mm"] * 0.018)
            active_reduction = min(0.34, candidate["rpic_bias"] + candidate["plasma_bias"])
            cooling_reduction = min(0.26, candidate["coolant_mass_flow_kg_s"] * 0.105)
            optimized_heat = baseline_heat * radius_factor * sweep_factor * edge_factor * (1.0 - active_reduction) * (1.0 - cooling_reduction)
            predicted_temp = 260.0 + optimized_heat * 0.00042 / max(material["conductivity_w_mk"], 0.1)
            margin = (material["max_temp_k"] - predicted_temp) / material["max_temp_k"]
            lift_to_drag = (candidate["reference_area_m2"] / baseline_area) * (1.72 / max(candidate["drag_coefficient"], 0.1))
            heat_reduction = 1.0 - optimized_heat / max(baseline_heat, 1.0)
            score = 0.48 * heat_reduction + 0.24 * max(0.0, margin) + 0.18 * min(1.0, lift_to_drag / 4.8) + 0.1 * material["sustainability"]
            result = {
                **candidate,
                "score": score,
                "optimized_heat": optimized_heat,
                "predicted_temp": predicted_temp,
                "thermal_margin": margin,
                "lift_to_drag": lift_to_drag,
                "heat_reduction": heat_reduction,
            }
            if best is None or result["score"] > best["score"]:
                best = result

        assert best is not None
        material = MATERIALS[best["material_id"]]
        heat_reduction_pct = round(best["heat_reduction"] * 100.0, 1)
        optimized_heat = round(best["optimized_heat"], 2)

        components = [
            {"id": "bow_shock", "name": "Attached Bow Shock", "role": "shock shaping", "x": 10, "y": 48, "color": "#ff5f3b", "temp_k": round(best["predicted_temp"] + 320), "status": "managed"},
            {"id": "nose", "name": "Blunt Ceramic Nose", "role": "radius heating control", "x": 18, "y": 52, "color": "#ff4d4d", "temp_k": round(best["predicted_temp"] + 180), "status": "critical watch"},
            {"id": "tps", "name": "UHTC TPS Tile Array", "role": "radiative barrier", "x": 34, "y": 42, "color": "#ff9900", "temp_k": round(best["predicted_temp"]), "status": "nominal"},
            {"id": "rpic", "name": "RPIC Plasma Fence", "role": "ionized boundary control", "x": 48, "y": 35, "color": "#00e08a", "temp_k": round(best["predicted_temp"] - 120), "status": "active"},
            {"id": "cooling", "name": "Zonal Regen Cooling", "role": "leading-edge heat sink", "x": 56, "y": 45, "color": "#20d7f2", "temp_k": round(best["predicted_temp"] - 180), "status": "active"},
            {"id": "scramjet", "name": "Variable-Geometry Scramjet", "role": "low-drag propulsion", "x": 74, "y": 56, "color": "#ff7a1a", "temp_k": round(best["predicted_temp"] - 90), "status": "throttled"},
            {"id": "nozzle", "name": "Expansion Nozzle Assembly", "role": "pressure recovery", "x": 91, "y": 49, "color": "#a65cff", "temp_k": round(best["predicted_temp"] - 260), "status": "nominal"},
        ]

        return {
            "model_stage": "surrogate-ensemble-v0.3",
            "design_id": "regen_hx2_prize_waverider",
            "name": best["name"],
            "score": round(best["score"], 3),
            "predicted": {
                "baseline_heat_flux_w_m2": round(baseline_heat, 2),
                "optimized_heat_flux_w_m2": optimized_heat,
                "heat_reduction_pct": heat_reduction_pct,
                "surface_temp_k": round(best["predicted_temp"], 1),
                "thermal_margin": round(best["thermal_margin"], 3),
                "lift_to_drag": round(best["lift_to_drag"], 2),
                "drag_coefficient": round(best["drag_coefficient"], 3),
                "cooling_power_kw": round(90 + best["coolant_mass_flow_kg_s"] * 285, 1),
            },
            "geometry": {
                "nose_radius_m": best["nose_radius_m"],
                "leading_edge_radius_mm": best["leading_edge_radius_mm"],
                "wing_sweep_deg": best["wing_sweep_deg"],
                "compression_ramp_deg": best["compression_ramp_deg"],
                "reference_area_m2": best["reference_area_m2"],
                "wetted_area_m2": round(best["reference_area_m2"] * 2.15, 1),
            },
            "materials": {
                "nose": material["name"],
                "leading_edges": "Rhenium-Iridium capped UHTC",
                "skin": "Carbon-carbon acreage TPS with emissive coating",
                "coolant": best["coolant"],
            },
            "components": components,
            "recommendations": [
                f"Use {best['nose_radius_m']:.2f} m ogival nose radius to lower stagnation heating.",
                f"Hold wing sweep near {best['wing_sweep_deg']} deg to spread leading-edge heat.",
                "Route regenerative coolant first through nose and leading-edge zones.",
                "Run RPIC and plasma shielding together during Mach 6+ climbout.",
            ],
            "mission_patch": {
                "vehicle": {
                    "name": "REGEN-HX2 Prize Waverider",
                    "nose_radius_m": best["nose_radius_m"],
                    "reference_area_m2": best["reference_area_m2"],
                    "drag_coefficient": best["drag_coefficient"],
                },
                "tps": {
                    "material_id": best["material_id"],
                    "thickness_mm": 56,
                    "surface_area_m2": round(best["reference_area_m2"] * 2.15, 1),
                },
                "cooling": {
                    "enabled": True,
                    "coolant": best["coolant"],
                    "mass_flow_kg_s": best["coolant_mass_flow_kg_s"],
                },
            },
        }
