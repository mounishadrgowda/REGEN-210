# Model Registry

Place trained artifacts here when the demo evolves beyond heuristic ML stubs.

Recommended layout:

```text
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
```

For hackathon judging, keep the API response field `model_stage` visible so judges understand which outputs are mock surrogates and which are trained models.

