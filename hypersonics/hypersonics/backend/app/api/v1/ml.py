from fastapi import APIRouter
from pydantic import BaseModel

from app.ml.inference import MLInferenceAdapter
from app.schemas.digital_twin import SimulationStartRequest

router = APIRouter()
adapter = MLInferenceAdapter()


class MaterialRecommendationRequest(BaseModel):
    heat_flux_w_m2: float = 1_800_000
    sustainability_weight: float = 0.35


class HeatPredictionRequest(BaseModel):
    current_temp_k: float = 1450
    cooling_efficiency: float = 0.42
    horizon_s: int = 30


class DesignGenerationRequest(BaseModel):
    mission: SimulationStartRequest | None = None


@router.post("/material-recommendation")
async def material_recommendation(request: MaterialRecommendationRequest) -> dict:
    return {
        "model_stage": "demo-surrogate",
        "ranked_materials": adapter.recommend_materials(request.heat_flux_w_m2, request.sustainability_weight),
    }


@router.post("/heat-prediction")
async def heat_prediction(request: HeatPredictionRequest) -> dict:
    points = []
    for idx in range(1, 7):
        t = idx * request.horizon_s / 6
        temp = request.current_temp_k * (1 + 0.009 * idx) - request.cooling_efficiency * 9 * idx
        points.append({"time_s": round(t, 1), "predicted_temp_k": round(temp, 1)})
    return {"model_stage": "demo-surrogate", "forecast": points}


@router.post("/anomaly-detection")
async def anomaly_detection(payload: dict) -> dict:
    heat = float(payload.get("heat_flux_w_m2", 0))
    cooling = float(payload.get("cooling_efficiency", 0))
    score = min(1.0, max(0.0, heat / 4_000_000 - cooling * 0.25))
    return {
        "model_stage": "demo-surrogate",
        "anomaly_score": round(score, 3),
        "explanation": "High heating with insufficient cooling raises anomaly score.",
    }


@router.post("/design-generator")
async def design_generator(request: DesignGenerationRequest) -> dict:
    mission_payload = request.mission.model_dump() if request.mission else None
    return adapter.generate_design(mission_payload)
