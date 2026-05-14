from fastapi import APIRouter

from app.schemas.digital_twin import (
    CoolingState,
    DigitalTwinState,
    AircraftState,
    TPSConfig,
    TPSEvaluateRequest,
    VehicleConfig,
)
from app.simulation.engine import SimulationEngine

router = APIRouter()


@router.post("/evaluate")
async def evaluate_tps(request: TPSEvaluateRequest) -> dict:
    engine = SimulationEngine()
    state = DigitalTwinState(
        simulation_id="single_eval",
        mission_id="tps_eval",
        vehicle=VehicleConfig(nose_radius_m=request.nose_radius_m),
        tps=TPSConfig(material_id=request.material_id, thickness_mm=request.thickness_mm),
        aircraft=AircraftState(mach=request.mach, altitude_m=request.altitude_m, angle_of_attack_deg=4.0),
        cooling=CoolingState(mass_flow_kg_s=request.coolant_mass_flow_kg_s),
    )
    state = engine.tick(state, 0.2)
    return {
        "heat_flux_w_m2": round(state.thermal.heat_flux_w_m2, 2),
        "wall_temperature_k": round(state.thermal.max_surface_temp_k, 2),
        "thermal_margin": round(state.thermal.thermal_margin, 3),
        "cooling_efficiency": round(state.cooling.efficiency, 3),
        "failure_warning": state.risk.failure_warning,
        "recommended_action": state.risk.recommended_action,
    }

