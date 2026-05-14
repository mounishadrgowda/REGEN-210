# API Architecture

Base URL: `/api/v1`

## Simulation APIs

### `POST /simulations/start`

Starts a mission simulation.

Request:

```json
{
  "mission_id": "demo-mission-001",
  "vehicle": {
    "name": "AETHER-HX1",
    "nose_radius_m": 0.35,
    "reference_area_m2": 22.0
  },
  "initial_conditions": {
    "mach": 6.8,
    "altitude_m": 31000,
    "angle_of_attack_deg": 4.0,
    "duration_s": 180
  },
  "tps": {
    "material_id": "c_phenolic",
    "thickness_mm": 42,
    "surface_area_m2": 48.5
  },
  "cooling": {
    "enabled": true,
    "coolant": "liquid_hydrogen",
    "mass_flow_kg_s": 0.8
  }
}
```

Response:

```json
{
  "simulation_id": "sim_20260514_001",
  "status": "running",
  "telemetry_ws": "/api/v1/telemetry/ws?simulation_id=sim_20260514_001"
}
```

### `POST /simulations/tick`

Runs one deterministic tick for testing.

### `GET /simulations/{simulation_id}/state`

Returns the latest digital twin state snapshot.

### `POST /simulations/{simulation_id}/stop`

Stops a running simulation.

## TPS APIs

### `POST /tps/evaluate`

Request:

```json
{
  "mach": 7.2,
  "altitude_m": 28000,
  "nose_radius_m": 0.35,
  "material_id": "c_phenolic",
  "thickness_mm": 42,
  "coolant_mass_flow_kg_s": 0.8
}
```

Response:

```json
{
  "heat_flux_w_m2": 1924550.4,
  "wall_temperature_k": 1490.2,
  "thermal_margin": 0.31,
  "cooling_efficiency": 0.42,
  "failure_warning": false,
  "recommended_action": "Maintain current TPS profile"
}
```

## ML Inference APIs

### `POST /ml/material-recommendation`

Returns ranked TPS materials.

### `POST /ml/heat-prediction`

Returns a future heat prediction curve.

### `POST /ml/anomaly-detection`

Returns anomaly score and explanation.

Demo rule: label these as "AI surrogate preview" unless a trained model is connected.

## Telemetry APIs

### `GET /telemetry/latest`

Returns latest twin snapshot.

### `WebSocket /telemetry/ws`

Pushes live telemetry.

Message:

```json
{
  "type": "telemetry.tick",
  "simulation_id": "sim_20260514_001",
  "time_s": 42,
  "state": {
    "aircraft": { "mach": 6.9, "altitude_m": 30200 },
    "thermal": { "max_surface_temp_k": 1460, "heat_flux_w_m2": 1810000 },
    "cooling": { "efficiency": 0.41 },
    "risk": { "level": "guarded", "score": 0.38 }
  }
}
```

## Visualization APIs

### `GET /visualization/heatmap/{simulation_id}`

Returns coarse grid values for a frontend thermal overlay.

### `GET /visualization/shockwave/{simulation_id}`

Returns cone angle and intensity values for visual animation.

## Reports

### `POST /reports/generate`

Creates a summary report from a simulation state.

