class RPICPlugin:
    name = "rpic"

    def _slew(self, previous: float, target: float, dt_s: float, max_rate_per_s: float, response_s: float) -> float:
        dt = max(0.02, min(dt_s, 1.0))
        alpha = dt / (response_s + dt)
        filtered = previous + (target - previous) * alpha
        max_delta = max_rate_per_s * dt
        return previous + max(-max_delta, min(max_delta, filtered - previous))

    def update(self, state, dt_s: float):
        if not state.rpic.enabled or state.thermal.heat_flux_w_m2 <= 0:
            state.rpic.plasma_density_m3 = 0
            state.rpic.ionization_fraction = 0
            state.rpic.heat_flux_reduction = 0
            state.rpic.control_effort = 0
            state.rpic.power_draw_kw = 0
            return state

        magnetic_field_t = max(0.0, min(5.0, state.rpic.magnetic_field_t))
        mach_over_entry = max(0.0, state.aircraft.mach - 5.0)
        heat_load = min(1.0, state.thermal.heat_flux_w_m2 / 3_000_000.0)
        magnetic_authority = 1.0 - 1.0 / (1.0 + magnetic_field_t * 0.65)
        target_control_effort = min(1.0, 0.13 * mach_over_entry + 0.45 * heat_load + magnetic_authority * 0.28)
        target_ionization_fraction = min(0.34, 0.04 + target_control_effort * 0.2 + magnetic_authority * 0.08)
        target_heat_flux_reduction = min(0.26, 0.025 + target_ionization_fraction * 0.44 + magnetic_authority * 0.08)
        control_effort = self._slew(state.rpic.control_effort, target_control_effort, dt_s, 0.22, 1.5)
        ionization_fraction = self._slew(state.rpic.ionization_fraction, target_ionization_fraction, dt_s, 0.08, 1.8)
        heat_flux_reduction = self._slew(state.rpic.heat_flux_reduction, target_heat_flux_reduction, dt_s, 0.04, 2.0)
        target_power_kw = 85.0 + target_control_effort * 360.0 + magnetic_field_t**2 * 42.0
        power_draw_kw = self._slew(state.rpic.power_draw_kw, target_power_kw, dt_s, 300.0, 1.2)

        state.rpic.magnetic_field_t = round(magnetic_field_t, 2)
        state.rpic.control_effort = round(control_effort, 3)
        state.rpic.ionization_fraction = round(ionization_fraction, 3)
        state.rpic.heat_flux_reduction = round(heat_flux_reduction, 3)
        state.rpic.plasma_density_m3 = round(1.0e17 * (1.0 + control_effort * 8.0 + magnetic_field_t * 0.75), 2)
        state.rpic.power_draw_kw = round(power_draw_kw, 2)
        state.thermal.heat_flux_w_m2 *= 1.0 - heat_flux_reduction
        return state


def register(registry):
    registry.add_module("rpic", RPICPlugin(), phase="post_thermal")
