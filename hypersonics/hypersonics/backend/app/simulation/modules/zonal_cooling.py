from app.schemas.digital_twin import DigitalTwinState
from app.schemas.zonal_cooling import CoolingZoneState
from app.simulation.materials import get_material


ZONE_PROFILES = (
    ("nose", 0.43, 1.0),
    ("leading_edges", 0.34, 0.78),
    ("body", 0.23, 0.48),
)


class ZonalCoolingModule:
    name = "zonal_cooling"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        if not state.zonal_cooling.enabled or state.thermal.heat_flux_w_m2 <= 0:
            state.zonal_cooling.zones = []
            state.zonal_cooling.active_zone = "none"
            state.zonal_cooling.balance_quality = 1
            state.zonal_cooling.max_zone_temp_k = state.thermal.max_surface_temp_k
            state.zonal_cooling.min_zone_margin = state.thermal.thermal_margin
            return state

        material = get_material(state.tps.material_id)
        max_temp_k = material["max_temp_k"]
        base_flux = state.thermal.heat_flux_w_m2
        total_heat_removed = state.cooling.heat_removed_w_m2 if state.cooling.enabled else 0
        cooling_capacity = min(0.85, total_heat_removed / base_flux) if base_flux > 0 else 0

        zones: list[CoolingZoneState] = []
        hottest_zone = "nose"
        max_zone_temp = 0.0
        min_margin = 1.0
        aggregate_net_flux = 0.0

        for name, coolant_fraction, heat_bias in ZONE_PROFILES:
            zone_heat_flux = base_flux * heat_bias
            zone_efficiency = min(0.9, cooling_capacity * (0.75 + coolant_fraction))
            zone_net_flux = zone_heat_flux * (1.0 - zone_efficiency)
            aggregate_net_flux += zone_net_flux * coolant_fraction
            surface_temp_k = 240.0 + zone_net_flux * 0.00032
            surface_temp_k = min(surface_temp_k, state.aerodynamic.stagnation_temperature_k * 1.15)
            thermal_margin = (max_temp_k - surface_temp_k) / max_temp_k

            if surface_temp_k > max_zone_temp:
                max_zone_temp = surface_temp_k
                hottest_zone = name
            min_margin = min(min_margin, thermal_margin)

            if thermal_margin < 0.08:
                status = "critical"
            elif thermal_margin < 0.22:
                status = "guarded"
            else:
                status = "nominal"

            zones.append(
                CoolingZoneState(
                    name=name,
                    heat_flux_w_m2=round(zone_heat_flux, 2),
                    coolant_fraction=coolant_fraction,
                    efficiency=round(zone_efficiency, 3),
                    surface_temp_k=round(surface_temp_k, 2),
                    thermal_margin=round(thermal_margin, 3),
                    status=status,
                )
            )

        state.zonal_cooling.zones = zones
        state.zonal_cooling.active_zone = hottest_zone
        state.zonal_cooling.max_zone_temp_k = round(max_zone_temp, 2)
        state.zonal_cooling.min_zone_margin = round(min_margin, 3)
        state.zonal_cooling.balance_quality = round(max(0.0, min(1.0, 1.0 - (max_zone_temp - state.thermal.max_surface_temp_k) / max(max_zone_temp, 1))), 3)
        state.thermal.net_heat_flux_w_m2 = min(state.thermal.net_heat_flux_w_m2, aggregate_net_flux)
        return state
