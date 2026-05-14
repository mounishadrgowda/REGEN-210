# AI/ML Integration Strategy

## Where Models Live

```text
ml/
  models/
    registry.json
    heat_predictor/
      v0.1/
        model.onnx
        model_card.md
    material_recommender/
      v0.1/
        model.pkl
        model_card.md
  training/
    train_heat_predictor.py
    train_material_recommender.py
```

## Model Loading

The backend uses an ML adapter. Today it returns explainable mock predictions. Later it can load:
- scikit-learn `.pkl`
- PyTorch `.pt`
- ONNX Runtime `.onnx`
- remote inference endpoint

## Inference Pipeline

```text
Twin State -> Feature Builder -> Model Registry -> Inference Adapter
           -> Prediction + Confidence + Explanation -> Twin AI State
```

## Future ML Modules

| Model | Inputs | Output | Demo Implementation |
| --- | --- | --- | --- |
| TPS Material Recommendation | Heat flux, temp, mass budget, sustainability target | Ranked materials | Rule-based |
| Heat Prediction | Last N telemetry ticks | Future temp curve | Polynomial/exponential surrogate |
| Failure Prediction | Thermal margin, stress, duration | Failure probability | Logistic heuristic |
| Surrogate Aerodynamic Model | Mach, altitude, geometry | heat coefficient | Mock regressor |
| RL Optimization | mission constraints | cooling/material policy | Visual-only |
| Anomaly Detection | telemetry vector | anomaly score | z-score heuristic |

## Dataset Structure

```text
datasets/
  sample/
    demo_telemetry.jsonl
  schemas/
    telemetry.schema.json
  raw/
  processed/
  features/
```

## Model Versioning

Use semantic versions and model cards:

```json
{
  "model_id": "heat_predictor",
  "version": "0.1.0",
  "stage": "demo",
  "artifact": "ml/models/heat_predictor/v0.1/model.onnx",
  "features": ["mach", "altitude_m", "heat_flux_w_m2", "cooling_efficiency"]
}
```

