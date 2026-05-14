import math

from app.schemas.digital_twin import DigitalTwinState


# --- ISO 2533-1975 standard atmosphere (up to 86 km) ---
def _iso_atmosphere(altitude_m: float) -> tuple[float, float, float]:
    """Returns (temperature_K, pressure_Pa, density_kg_m3)."""
    g0 = 9.80665
    R  = 287.058          # J/(kg·K)

    # Layer boundaries and lapse rates [m, K, K/m]
    layers = [
        (0,      288.15, -0.0065),   # Troposphere
        (11000,  216.65,  0.0),      # Tropopause
        (20000,  216.65,  0.001),    # Stratosphere 1
        (32000,  228.65,  0.0028),   # Stratosphere 2
        (47000,  270.65,  0.0),      # Stratopause
        (51000,  270.65, -0.0028),   # Mesosphere 1
        (71000,  214.65, -0.002),    # Mesosphere 2
        (86000,  186.87,  0.0),      # Mesopause (clamp)
    ]

    # Sea-level reference
    P0, T0_sl = 101325.0, 288.15
    T, P = T0_sl, P0
    h = min(max(altitude_m, 0.0), 86000.0)

    for i, (h_base, T_base, lapse) in enumerate(layers):
        h_top = layers[i + 1][0] if i + 1 < len(layers) else 86000.0
        if h <= h_top:
            dh = h - h_base
            if abs(lapse) < 1e-10:             # isothermal layer
                T = T_base
                P = P * math.exp(-g0 * dh / (R * T_base))
            else:
                T = T_base + lapse * dh
                P = P * (T / T_base) ** (-g0 / (lapse * R))
            break
        else:
            dh = h_top - h_base
            if abs(lapse) < 1e-10:
                T_next = T_base
                P = P * math.exp(-g0 * dh / (R * T_base))
            else:
                T_next = T_base + lapse * dh
                P = P * (T_next / T_base) ** (-g0 / (lapse * R))
            T = T_next

    density = P / (R * T)
    return T, P, density


class AerodynamicsModule:
    name = "aerodynamics"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        alt = state.aircraft.altitude_m

        # ISO atmosphere
        T_static, _, density = _iso_atmosphere(alt)

        # Local speed of sound: a = sqrt(gamma * R * T)
        gamma, R = 1.4, 287.058
        speed_of_sound = math.sqrt(gamma * R * T_static)

        mach = max(state.aircraft.mach, 0.01)
        velocity = mach * speed_of_sound

        dynamic_pressure = 0.5 * density * velocity ** 2

        # Mach-angle of shock cone (attached shock assumption)
        shock_angle = math.degrees(math.asin(min(1.0, 1.0 / max(mach, 1.01))))

        # Isentropic stagnation temperature (exact, not approximation)
        stagnation_temperature = T_static * (1.0 + 0.5 * (gamma - 1.0) * mach ** 2)

        state.aircraft.velocity_m_s           = velocity
        state.aerodynamic.density_kg_m3       = density
        state.aerodynamic.dynamic_pressure_pa = dynamic_pressure
        state.aerodynamic.shock_cone_angle_deg = shock_angle
        state.aerodynamic.stagnation_temperature_k = stagnation_temperature
        return state