class PlasmaShieldingPlugin:
    name = "plasma_shielding"

    def _slew(self, previous: float, target: float, dt_s: float, max_rate_per_s: float, response_s: float) -> float:
        dt = max(0.02, min(dt_s, 1.0))
        alpha = dt / (response_s + dt)
        filtered = previous + (target - previous) * alpha
        max_delta = max_rate_per_s * dt
        return previous + max(-max_delta, min(max_delta, filtered - previous))

    def update(self, state, dt_s: float):
        # Demo subsystem: a future electromagnetic/plasma layer reduces exposed heat flux.
        if not state.plasma_shielding.enabled:
            state.plasma_shielding.reduction_factor = 0
            state.plasma_shielding.hall_parameter = 0
            state.plasma_shielding.power_draw_kw = 0
            return state

        magnetic_field_t = max(0.0, min(5.0, state.plasma_shielding.magnetic_field_t))
        mach_factor = min(0.1, max(0.015, (state.aircraft.mach - 5.0) * 0.015))
        target_hall = magnetic_field_t * max(0.0, state.aircraft.mach - 4.0) / 7.5
        magnetic_gain = 1.0 - 1.0 / (1.0 + target_hall)
        target_reduction = min(0.24, mach_factor + magnetic_gain * 0.15)
        hall_parameter = self._slew(state.plasma_shielding.hall_parameter, target_hall, dt_s, 0.9, 1.4)
        reduction_factor = self._slew(state.plasma_shielding.reduction_factor, target_reduction, dt_s, 0.035, 1.8)
        target_power_kw = 42.0 + magnetic_field_t**2 * 38.0 + target_reduction * 260.0
        power_draw_kw = self._slew(state.plasma_shielding.power_draw_kw, target_power_kw, dt_s, 280.0, 1.2)
        heat_flux_before = state.thermal.heat_flux_w_m2
        state.thermal.heat_flux_w_m2 *= 1.0 - reduction_factor
        state.plasma_shielding.hall_parameter = round(hall_parameter, 3)
        state.plasma_shielding.reduction_factor = round(reduction_factor, 3)
        state.plasma_shielding.heat_flux_before_w_m2 = round(heat_flux_before, 2)
        state.plasma_shielding.heat_flux_after_w_m2 = round(state.thermal.heat_flux_w_m2, 2)
        state.plasma_shielding.power_draw_kw = round(power_draw_kw, 2)
        return state


def register(registry):
    registry.add_module("plasma_shielding", PlasmaShieldingPlugin(), phase="post_thermal")
