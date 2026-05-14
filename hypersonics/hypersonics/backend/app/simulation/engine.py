from uuid import uuid4

from app.ml.inference import MLInferenceAdapter
from app.plugins.registry import PluginRegistry
from app.schemas.digital_twin import (
    AircraftState,
    CoolingState,
    DigitalTwinState,
    SimulationStartRequest,
)
from app.simulation.modules.aerodynamics import AerodynamicsModule
from app.simulation.modules.cooling import RegenerativeCoolingModule
from app.simulation.modules.risk import StructuralRiskModule
from app.simulation.modules.sustainability import SustainabilityModule
from app.simulation.modules.thermal import ThermalProtectionModule
from app.simulation.modules.zonal_cooling import ZonalCoolingModule


class SimulationEngine:
    def __init__(self) -> None:
        from plugins.rpic.plugin import RPICPlugin

        self.plugin_registry = PluginRegistry()
        self.aerodynamics = AerodynamicsModule()
        self.thermal = ThermalProtectionModule()
        self.cooling = RegenerativeCoolingModule()
        self.risk = StructuralRiskModule()
        self.sustainability = SustainabilityModule()
        self.ml = MLInferenceAdapter()
        self.zonal_cooling = ZonalCoolingModule()
    # Register RPIC — replaces the old plasma_shielding stub
        self.plugin_registry.add_module("rpic", RPICPlugin(), phase="post_thermal")
    # adaptive_materials still runs post_risk
        from plugins.adaptive_materials.plugin import AdaptiveMaterialsPlugin
        self.plugin_registry.add_module(
            "adaptive_materials", AdaptiveMaterialsPlugin(), phase="post_risk"
        ):

def create_state(self, request: SimulationStartRequest) -> DigitalTwinState:
    from app.schemas.rpic import RPICState
    simulation_id = f"sim_{uuid4().hex[:10]}"
    state = DigitalTwinState(
        simulation_id=simulation_id,
        mission_id=request.mission_id,
        vehicle=request.vehicle,
        tps=request.tps,
        aircraft=AircraftState(
            mach=request.initial_conditions.mach,
            altitude_m=request.initial_conditions.altitude_m,
            angle_of_attack_deg=request.initial_conditions.angle_of_attack_deg,
        ),
        cooling=CoolingState(
            enabled=request.cooling.enabled,
            coolant=request.cooling.coolant,
            mass_flow_kg_s=request.cooling.mass_flow_kg_s,
        ),
        rpic=RPICState(),
    )
    # Wire the operator-supplied RPIC config into the plugin instance
    for module in self.plugin_registry._phases.get("post_thermal", []):
        if getattr(module, "name", None) == "rpic":
            module.config = request.rpic
    return state

    def tick(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
    state.time_s += dt_s
    state.aircraft.mach += 0.015
    state.aircraft.altitude_m = max(18000, state.aircraft.altitude_m - 9.0 * dt_s)

    state = self.aerodynamics.update(state, dt_s)
    state = self.thermal.update(state, dt_s)
    state = self.plugin_registry.run_phase("post_thermal", state, dt_s)  # RPIC runs here
    state = self.zonal_cooling.update(state, dt_s)      # ← replaces RegenerativeCoolingModule
    state = self.thermal.update(state, 0)               # recompute wall temp with net flux
    state = self.risk.update(state, dt_s)
    state = self.sustainability.update(state, dt_s)
    state = self.ml.update(state, dt_s)
    state = self.plugin_registry.run_phase("post_risk", state, dt_s)
    return state