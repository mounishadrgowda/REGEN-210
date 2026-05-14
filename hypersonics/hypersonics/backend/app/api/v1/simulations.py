from fastapi import APIRouter, HTTPException

from app.schemas.digital_twin import SimulationStartRequest
from app.services.simulation_service import simulation_service

router = APIRouter()


@router.post("/start")
async def start_simulation(request: SimulationStartRequest) -> dict:
    state = await simulation_service.start(request)
    return {
        "simulation_id": state.simulation_id,
        "mission_id": state.mission_id,
        "mission_generated": True,
        "status": "running",
        "telemetry_ws": f"/api/v1/telemetry/ws?simulation_id={state.simulation_id}",
    }


@router.post("/{simulation_id}/tick")
async def tick_simulation(simulation_id: str) -> dict:
    if simulation_id not in simulation_service.states:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation_service.tick_once(simulation_id).model_dump()


@router.get("/{simulation_id}/state")
async def get_state(simulation_id: str) -> dict:
    state = simulation_service.latest(simulation_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return state.model_dump()


@router.post("/{simulation_id}/stop")
async def stop_simulation(simulation_id: str) -> dict:
    ok = simulation_service.stop(simulation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {"simulation_id": simulation_id, "status": "stopped"}
