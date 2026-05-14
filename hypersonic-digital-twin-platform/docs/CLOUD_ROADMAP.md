# Future Cloud Architecture

## Current Hackathon Architecture

```text
React frontend -> FastAPI backend -> in-memory simulation -> WebSocket telemetry
```

## Cloud-Ready Evolution

```text
API Gateway
  -> Simulation Orchestrator
  -> Physics Workers
  -> ML Inference Service
  -> Telemetry Streaming Service
  -> Report Service
  -> PostgreSQL/TimescaleDB
  -> Object Storage for reports and model artifacts
```

## Microservices

| Service | Purpose |
| --- | --- |
| API Gateway | Auth, routing, REST contracts |
| Simulation Orchestrator | Session lifecycle and tick scheduling |
| Aerothermal Worker | CFD/surrogate computation |
| TPS Worker | Material and cooling simulation |
| ML Inference Server | GPU-backed predictions |
| Telemetry Service | WebSocket fanout |
| Report Service | PDF/HTML reports |

## Kubernetes Path

- `frontend` deployment with CDN/static hosting later.
- `backend-api` deployment.
- `simulation-worker` deployment with CPU autoscaling.
- `ml-inference` deployment with GPU node pool.
- Redis for Pub/Sub and cache.
- Postgres + TimescaleDB for telemetry.
- S3-compatible object storage for reports and model artifacts.

## Distributed Simulation

Split simulations by mission, geometry, or parameter sweep. Use queue workers for optimization runs and stream partial results to the dashboard.

