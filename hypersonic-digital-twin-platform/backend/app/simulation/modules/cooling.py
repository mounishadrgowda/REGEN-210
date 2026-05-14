from app.schemas.digital_twin import DigitalTwinState


COOLANT_CP = {
    "liquid_hydrogen": 14300.0,
    "water_glycol": 3600.0,
    "methane": 3500.0,
}


class RegenerativeCoolingModule:
    name = "regenerative_cooling"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        if not state.cooling.enabled or state.thermal.heat_flux_w_m2 <= 0:
            state.cooling.heat_removed_w_m2 = 0
            state.cooling.efficiency = 0
            state.thermal.net_heat_flux_w_m2 = state.thermal.heat_flux_w_m2
            return state

        cp = COOLANT_CP.get(state.cooling.coolant, COOLANT_CP["liquid_hydrogen"])
        delta_t_k = 120.0
        heat_removed = state.cooling.mass_flow_kg_s * cp * delta_t_k / state.tps.surface_area_m2
        efficiency = max(0.0, min(0.85, heat_removed / state.thermal.heat_flux_w_m2))

        state.cooling.heat_removed_w_m2 = heat_removed
        state.cooling.efficiency = efficiency
        state.thermal.net_heat_flux_w_m2 = state.thermal.heat_flux_w_m2 * (1 - efficiency)
        return state

