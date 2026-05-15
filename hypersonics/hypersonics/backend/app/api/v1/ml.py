from fastapi import APIRouter
from pydantic import BaseModel

from app.ml.inference import MLInferenceAdapter

router  = APIRouter()
adapter = MLInferenceAdapter()     # loaded once at startup


class MaterialRecommendationRequest(BaseModel):
    heat_flux_w_m2:       float = 1_800_000
    net_heat_flux_w_m2:   float = 900_000
    cooling_efficiency:   float = 0.42
    thickness_mm:         float = 42.0
    nose_radius_m:        float = 0.35
    aoa_deg:              float = 4.0
    sustainability_weight: float = 0.35


class HeatPredictionRequest(BaseModel):
    mach:               float = 6.8
    altitude_m:         float = 31_000
    heat_flux_w_m2:     float = 1_800_000
    net_heat_flux_w_m2: float = 900_000
    cooling_efficiency: float = 0.42
    thickness_mm:       float = 42.0
    nose_radius_m:      float = 0.35
    mat_conductivity:   float = 0.7


class FailurePredictionRequest(BaseModel):
    thermal_margin:      float = 0.35
    dynamic_pressure_pa: float = 40_000
    heat_flux_w_m2:      float = 1_800_000
    net_heat_flux_w_m2:  float = 900_000
    cooling_efficiency:  float = 0.42
    mach:                float = 6.8
    altitude_m:          float = 31_000


@router.post("/material-recommendation")
async def material_recommendation(request: MaterialRecommendationRequest) -> dict:
    ranked = adapter.recommend_materials(
        heat_flux_w_m2=request.heat_flux_w_m2,
        net_heat_flux_w_m2=request.net_heat_flux_w_m2,
        cooling_efficiency=request.cooling_efficiency,
        thickness_mm=request.thickness_mm,
        nose_radius_m=request.nose_radius_m,
        aoa_deg=request.aoa_deg,
        sustainability_weight=request.sustainability_weight,
    )
    return {
        "model_stage":     adapter._recommender is not None and "trained-surrogate" or "demo-surrogate",
        "ranked_materials": ranked,
    }


@router.post("/heat-prediction")
async def heat_prediction(request: HeatPredictionRequest) -> dict:
    import math

    if adapter._heat is not None:
        model    = adapter._heat["model"]
        features = adapter._heat["features"]
        row = {
            "mach":               request.mach,
            "altitude_m":         request.altitude_m,
            "density_kg_m3":      1.225 * math.exp(-request.altitude_m / 8500.0),
            "heat_flux_w_m2":     request.heat_flux_w_m2,
            "net_heat_flux_w_m2": request.net_heat_flux_w_m2,
            "cooling_efficiency": request.cooling_efficiency,
            "thickness_mm":       request.thickness_mm,
            "mat_conductivity":   request.mat_conductivity,
            "nose_radius_m":      request.nose_radius_m,
        }
        X      = [[row[f] for f in features]]
        T_pred = float(model.predict(X)[0])
        points = [{"time_s": 0.0, "predicted_temp_k": round(T_pred, 1)}]
        model_stage = "trained-surrogate"
    else:
        points = []
        model_stage = "demo-surrogate"

    return {"model_stage": model_stage, "forecast": points}


@router.post("/failure-prediction")
async def failure_prediction(request: FailurePredictionRequest) -> dict:
    if adapter._failure is not None:
        model    = adapter._failure["model"]
        features = adapter._failure["features"]
        row = {
            "thermal_margin":      request.thermal_margin,
            "dynamic_pressure_pa": request.dynamic_pressure_pa,
            "heat_flux_w_m2":      request.heat_flux_w_m2,
            "net_heat_flux_w_m2":  request.net_heat_flux_w_m2,
            "cooling_efficiency":  request.cooling_efficiency,
            "mach":                request.mach,
            "altitude_m":          request.altitude_m,
        }
        X    = [[row[f] for f in features]]
        prob = float(model.predict_proba(X)[0][1])
        return {
            "model_stage":       "trained-surrogate",
            "failure_probability": round(prob, 3),
            "failure_predicted":   prob > 0.5,
        }

    # Heuristic fallback
    prob = min(0.98, (1.0 - request.thermal_margin) * 0.7
               + max(0, 0.1 - request.thermal_margin))
    return {
        "model_stage":       "demo-surrogate",
        "failure_probability": round(prob, 3),
        "failure_predicted":   prob > 0.5,
    }


@router.post("/anomaly-detection")
async def anomaly_detection(payload: dict) -> dict:
    import math
    q_mw      = float(payload.get("heat_flux_w_m2", 0)) / 1_000_000.0
    cooling   = float(payload.get("cooling_efficiency", 0))
    margin    = float(payload.get("thermal_margin", 0.5))

    z_cooling = abs(cooling - 0.42) / 0.22
    z_margin  = abs(margin  - 0.35) / 0.25
    z_flux    = abs(q_mw    - 2.5)  / 1.8
    rms       = math.sqrt((z_cooling**2 + z_margin**2 + z_flux**2) / 3.0)
    score     = round(min(1.0, rms / 3.0), 3)

    return {
        "model_stage":   "z-score envelope",
        "anomaly_score": score,
        "contributors": {
            "cooling_efficiency_z": round(z_cooling, 2),
            "thermal_margin_z":     round(z_margin, 2),
            "heat_flux_z":          round(z_flux, 2),
        },
        "explanation": (
            "Score is the RMS of z-scores across three telemetry channels "
            "normalised against expected operating envelope."
        ),
    }