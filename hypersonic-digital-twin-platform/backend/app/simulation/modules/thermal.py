import math

from app.schemas.digital_twin import DigitalTwinState
from app.simulation.materials import get_material


# --- Fay-Riddell stagnation-point heat flux ---
def _fay_riddell_heat_flux(rho: float, velocity: float, nose_radius: float) -> float:
    """
    Simplified Fay-Riddell stagnation-point heat transfer [W/m²].

    q = C_fr * sqrt(rho / R_n) * V^3

    The constant C_fr = 1.83e-4 is the classical Fay-Riddell coefficient
    for a non-catalytic wall in equilibrium air. This is the physically
    meaningful value (not a scaled demo number).

    Reference: Fay & Riddell, J. Aeronautical Sciences, 1958.
    """
    C_fr = 1.83e-4
    return C_fr * math.sqrt(max(rho, 1e-6) / max(nose_radius, 0.01)) * velocity ** 3


def _aoa_correction(base_flux: float, aoa_deg: float) -> float:
    """
    Off-stagnation correction for angle of attack.

    On windward panels, local heat flux increases roughly as:
        q_panel = q_stag * cos(aoa)^0.5  (windward)
        q_panel = q_stag * sin(aoa)^0.5  (leeward shadow, reduced)

    Here we apply a net increase to the integrated surface flux:
        factor = 1 + 0.5 * sin²(aoa)
    (Comes from averaging windward/leeward distributions over a cone body.)
    """
    aoa_rad = math.radians(abs(aoa_deg))
    aoa_factor = 1.0 + 0.5 * math.sin(aoa_rad) ** 2
    return base_flux * aoa_factor


def _wall_temperature(net_flux: float, material: dict, thickness_mm: float) -> float:
    """
    Steady-state 1-D conduction through the TPS tile to a cold structure.

    T_wall = T_structure + q_net * (thickness / conductivity)

    T_structure (cold-side) is approximated as the vehicle interior: ~350 K.
    Thickness converted mm → m.
    """
    T_structure = 350.0            # K, vehicle interior / cold side
    thickness_m = thickness_mm / 1000.0
    conductivity = max(material["conductivity_w_mk"], 0.1)
    T_wall = T_structure + net_flux * (thickness_m / conductivity)
    return T_wall


class ThermalProtectionModule:
    name = "thermal_protection"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        material    = get_material(state.tps.material_id)
        nose_radius = max(state.vehicle.nose_radius_m, 0.05)
        rho         = max(state.aerodynamic.density_kg_m3, 1e-6)
        velocity    = max(state.aircraft.velocity_m_s, 1.0)

        # 1. Fay-Riddell stagnation-point heat flux
        q_stag = _fay_riddell_heat_flux(rho, velocity, nose_radius)

        # 2. Angle-of-attack correction for off-stagnation panels
        heat_flux = _aoa_correction(q_stag, state.aircraft.angle_of_attack_deg)

        state.thermal.heat_flux_w_m2 = heat_flux

        # net_heat_flux is updated by cooling module; initialise on first tick
        if state.thermal.net_heat_flux_w_m2 <= 0:
            state.thermal.net_heat_flux_w_m2 = heat_flux

        # 3. 1-D conduction wall temperature
        wall_temp = _wall_temperature(
            state.thermal.net_heat_flux_w_m2,
            material,
            state.tps.thickness_mm,
        )
        # Physical ceiling: wall cannot exceed stagnation temperature
        wall_temp = min(wall_temp, state.aerodynamic.stagnation_temperature_k)

        state.thermal.max_surface_temp_k = wall_temp

        # 4. Integrate thermal load [MJ/m²]
        if dt_s > 0:
            state.thermal.thermal_load_mj_m2 += (
                state.thermal.net_heat_flux_w_m2 * dt_s / 1_000_000.0
            )

        # 5. Thermal margin vs material limit
        state.thermal.thermal_margin = max(
            0.0,
            (material["max_temp_k"] - wall_temp) / material["max_temp_k"],
        )
        return state