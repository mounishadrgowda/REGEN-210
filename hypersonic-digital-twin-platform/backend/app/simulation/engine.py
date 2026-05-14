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


class SimulationEngine:
    def __init__(self) -> None:
        self.plugin_registry = PluginRegistry()
        self.aerodynamics = AerodynamicsModule()
        self.thermal = ThermalProtectionModule()
        self.cooling = RegenerativeCoolingModule()
        self.risk = StructuralRiskModule()
        self.sustainability = SustainabilityModule()
        self.ml = MLInferenceAdapter()

    def create_state(self, request: SimulationStartRequest) -> DigitalTwinState:
        simulation_id = f"sim_{uuid4().hex[:10]}"
        return DigitalTwinState(
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
        )

    def tick(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        state.time_s += dt_s
        state.aircraft.mach += 0.015
        state.aircraft.altitude_m = max(18000, state.aircraft.altitude_m - 9.0 * dt_s)

        state = self.aerodynamics.update(state, dt_s)
        state = self.thermal.update(state, dt_s)
        state = self.plugin_registry.run_phase("post_thermal", state, dt_s)
        state = self.cooling.update(state, dt_s)
        state = self.thermal.update(state, 0)
        state = self.risk.update(state, dt_s)
        state = self.sustainability.update(state, dt_s)
        state = self.ml.update(state, dt_s)
        state = self.plugin_registry.run_phase("post_risk", state, dt_s)
        return state
