import math

from app.schemas.digital_twin import DigitalTwinState
from app.simulation.materials import get_material


class ThermalProtectionModule:
    name = "thermal_protection"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        material = get_material(state.tps.material_id)
        nose_radius = max(state.vehicle.nose_radius_m, 0.05)
        rho = max(state.aerodynamic.density_kg_m3, 0.00001)
        velocity = max(state.aircraft.velocity_m_s, 1.0)

        demo_scale = 3.95e-4
        heat_flux = demo_scale * math.sqrt(rho / nose_radius) * velocity**3
        heat_flux *= 1.0 + abs(state.aircraft.angle_of_attack_deg) * 0.025

        if dt_s > 0 or state.thermal.heat_flux_w_m2 <= 0:
            state.thermal.heat_flux_w_m2 = heat_flux
        if state.thermal.net_heat_flux_w_m2 <= 0:
            state.thermal.net_heat_flux_w_m2 = state.thermal.heat_flux_w_m2

        thickness_factor = max(0.2, 50.0 / max(state.tps.thickness_mm, 1.0))
        conductivity = max(material["conductivity_w_mk"], 0.1)
        wall_temp = 240.0 + (state.thermal.net_heat_flux_w_m2 * thickness_factor / conductivity) * 0.00055
        wall_temp = min(wall_temp, state.aerodynamic.stagnation_temperature_k * 1.15)

        state.thermal.max_surface_temp_k = wall_temp
        state.thermal.thermal_load_mj_m2 += state.thermal.net_heat_flux_w_m2 * dt_s / 1_000_000.0
        state.thermal.thermal_margin = (material["max_temp_k"] - wall_temp) / material["max_temp_k"]
        return state
