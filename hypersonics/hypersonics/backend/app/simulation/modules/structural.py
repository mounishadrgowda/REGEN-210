from app.schemas.digital_twin import DigitalTwinState
from app.simulation.materials import get_material


class StructuralMechanicsModule:
    name = "structural_mechanics"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        material = get_material(state.tps.material_id)
        temp_delta_k = max(0.0, state.thermal.max_surface_temp_k - 300.0)
        heat_load = max(0.0, state.thermal.thermal_load_mj_m2)
        pressure_ratio = min(1.8, state.aerodynamic.dynamic_pressure_pa / 95_000.0)
        panel_factor = max(0.65, 52.0 / max(state.tps.thickness_mm, 1.0))

        expansion_strain = temp_delta_k * 4.8e-6
        thermal_stress = expansion_strain * 72_000.0 * panel_factor
        joint_stress = thermal_stress * (0.42 + 0.34 * pressure_ratio)
        ablation_rate = max(0.0, state.thermal.net_heat_flux_w_m2 - 650_000.0) / 8_500_000.0

        state.structural.thermal_stress_mpa = round(thermal_stress, 2)
        state.structural.joint_stress_mpa = round(joint_stress, 2)
        state.structural.ablation_depth_mm = round(state.structural.ablation_depth_mm + ablation_rate * dt_s, 4)
        state.structural.fatigue_damage = round(
            min(1.0, state.structural.fatigue_damage + (joint_stress / 850.0) ** 2 * dt_s / 12_000.0 + heat_load * 0.000002),
            5,
        )
        state.structural.cycles = int(max(state.structural.cycles, state.thermal.thermal_load_mj_m2 // 24))
        state.structural.remaining_life_cycles = max(0, int(120 * (1.0 - state.structural.fatigue_damage) - state.structural.ablation_depth_mm * 7))
        state.structural.failure_probability = round(
            min(0.98, 0.42 * max(0.0, 1.0 - state.thermal.thermal_margin) + 0.35 * state.structural.fatigue_damage + 0.23 * min(1.0, joint_stress / 720.0)),
            3,
        )

        if state.zonal_cooling.active_zone != "none":
            state.structural.limiting_location = state.zonal_cooling.active_zone
        elif material["max_temp_k"] - state.thermal.max_surface_temp_k < 250:
            state.structural.limiting_location = "tps acreage"
        else:
            state.structural.limiting_location = "nose"

        return state
