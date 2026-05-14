from datetime import datetime, timezone

from fastapi import APIRouter

from app.services.simulation_service import simulation_service

router = APIRouter()


@router.post("/generate")
async def generate_report(payload: dict) -> dict:
    simulation_id = payload.get("simulation_id")
    state = simulation_service.latest(simulation_id)
    if state is None:
        return {"status": "error", "message": "Simulation not found"}

    return {
        "status": "generated",
        "report_id": f"report_{state.simulation_id}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "mission_id": state.mission_id,
            "risk_level": state.risk.level,
            "max_surface_temp_k": round(state.thermal.max_surface_temp_k, 1),
            "thermal_margin": round(state.thermal.thermal_margin, 3),
            "sustainability_score": state.sustainability.score,
            "recommended_action": state.risk.recommended_action,
        },
    }

