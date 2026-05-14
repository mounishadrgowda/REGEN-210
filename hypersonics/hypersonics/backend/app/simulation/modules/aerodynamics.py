import math

from app.schemas.digital_twin import DigitalTwinState


class AerodynamicsModule:
    name = "aerodynamics"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        speed_of_sound = 295.0
        velocity = state.aircraft.mach * speed_of_sound
        density = 1.225 * math.exp(-state.aircraft.altitude_m / 8500.0)
        dynamic_pressure = 0.5 * density * velocity**2
        shock_angle = math.degrees(math.asin(min(1.0, 1.0 / max(state.aircraft.mach, 1.01))))
        stagnation_temperature = 220.0 * (1 + 0.2 * state.aircraft.mach**2)

        state.aircraft.velocity_m_s = velocity
        state.aerodynamic.density_kg_m3 = density
        state.aerodynamic.dynamic_pressure_pa = dynamic_pressure
        state.aerodynamic.shock_cone_angle_deg = shock_angle
        state.aerodynamic.stagnation_temperature_k = stagnation_temperature
        return state

