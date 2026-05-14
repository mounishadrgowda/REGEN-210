import math

from fastapi import APIRouter

from app.services.simulation_service import simulation_service

router = APIRouter()


@router.get("/heatmap/{simulation_id}")
async def heatmap(simulation_id: str) -> dict:
    state = simulation_service.latest(simulation_id)
    peak = state.thermal.max_surface_temp_k if state else 1200
    grid = []
    for y in range(8):
        row = []
        for x in range(16):
            nose_bias = math.exp(-x / 5)
            leading_edge = 0.25 * math.sin(y / 7 * math.pi)
            row.append(round(peak * (0.35 + 0.55 * nose_bias + leading_edge), 1))
        grid.append(row)
    return {"simulation_id": simulation_id, "units": "kelvin", "grid": grid}


@router.get("/shockwave/{simulation_id}")
async def shockwave(simulation_id: str) -> dict:
    state = simulation_service.latest(simulation_id)
    mach = state.aircraft.mach if state else 6.8
    cone_angle = math.degrees(math.asin(min(1.0, 1.0 / mach)))
    return {
        "simulation_id": simulation_id,
        "mach": round(mach, 2),
        "cone_angle_deg": round(cone_angle, 2),
        "intensity": round(min(1.0, mach / 10), 3),
    }

