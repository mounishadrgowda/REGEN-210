# REGEN-TWIN Hypersonic Platform

REGEN-TWIN is a prototype digital twin for hypersonic vehicle thermal protection system (TPS) exploration. It combines a FastAPI simulation backend, a React/Vite mission console, live telemetry over WebSockets, surrogate ML endpoints, plugin-driven subsystem extensions, and markdown mission report generation.

The project is intended for early-stage engineering demos and hackathon-style exploration. The physics and ML layers are simplified surrogate models, not flight qualification tools.

## Highlights

- Start, tick, inspect, and stop hypersonic mission simulations.
- Evaluate TPS material, thickness, heating, cooling, risk, and recommended actions.
- Stream live telemetry to the frontend mission console over WebSockets.
- View dashboard metrics, thermal findings, charts, and a 3D vehicle design view.
- Generate downloadable markdown mission reports under `reports/generated/`.
- Extend simulation behavior through plugins such as adaptive materials and plasma shielding.
- Run locally with PowerShell helper scripts or through Docker Compose.

## Tech Stack

- Backend: Python, FastAPI, Pydantic, Uvicorn
- Frontend: React 18, TypeScript, Vite, Recharts, Three.js, lucide-react
- Realtime: FastAPI WebSockets
- Deployment starters: Docker Compose and Kubernetes manifests

## Project Structure

```text
hypersonic-digital-twin-platform/
  backend/                  FastAPI app, simulation engine, schemas, routers
  frontend/                 React/Vite mission console and 3D visualizations
  plugins/                  Optional subsystem plugins loaded at backend startup
  ml/                       Demo inference adapter, model registry, training stub
  datasets/                 Sample telemetry and schema definitions
  configs/                  Example runtime and simulation configuration
  deployment/               Docker and Kubernetes starter assets
  docs/                     Architecture, API, engine, plugin, and roadmap notes
  reports/                  Report templates and generated mission reports
  scripts/                  PowerShell development runners
```

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- npm
- PowerShell, if using the helper scripts
- Docker Desktop, optional for containerized startup

## Quick Start

From the repository root:

```powershell
.\scripts\run_app.ps1
```

The script creates a backend virtual environment if needed, installs missing backend and frontend dependencies, starts FastAPI on port `8000`, then starts Vite on port `5173`.

Open:

```text
http://127.0.0.1:5173
```

Useful local URLs:

- Frontend: `http://127.0.0.1:5173`
- API health check: `http://127.0.0.1:8000/health`
- Swagger docs: `http://127.0.0.1:8000/docs`
- Telemetry WebSocket: `ws://127.0.0.1:8000/api/v1/telemetry/ws`

## Manual Development Setup

Start the backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` traffic to `http://127.0.0.1:8000`, so the frontend can use relative API paths during local development.

## Docker Compose

From the repository root:

```powershell
docker compose -f deployment\docker\docker-compose.yml up --build
```

Services:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## API Overview

Main backend entrypoint: `backend/app/main.py`

Registered route groups:

- `GET /health`
- `POST /api/v1/simulations/start`
- `POST /api/v1/simulations/{simulation_id}/tick`
- `GET /api/v1/simulations/{simulation_id}/state`
- `POST /api/v1/simulations/{simulation_id}/stop`
- `POST /api/v1/tps/evaluate`
- `GET /api/v1/telemetry/latest`
- `WS /api/v1/telemetry/ws`
- `POST /api/v1/ml/material-recommendation`
- `POST /api/v1/ml/heat-prediction`
- `POST /api/v1/ml/anomaly-detection`
- `GET /api/v1/visualization/heatmap/{simulation_id}`
- `GET /api/v1/visualization/shockwave/{simulation_id}`
- `POST /api/v1/reports/generate`

## Frontend Workflow

The frontend mission console lets you:

- Adjust mission, vehicle, TPS, and cooling inputs.
- Start a live simulation and watch telemetry update.
- Inspect engineering findings, risk state, thermal load, heat flux, and cooling performance.
- Switch between the dashboard and 3D design views.
- Generate and download a markdown mission report once a simulation is running.

## Configuration

Example environment values live in `configs/env.example`.

The backend currently reads settings from environment variables through Pydantic settings:

- `APP_NAME`
- `SIMULATION_TICK_HZ`
- `CORS_ORIGINS`

Frontend API overrides:

- `VITE_API_BASE`, defaulting to `/api/v1`
- `VITE_WS_BASE`, listed in the example environment file for external deployments

## Testing

Run frontend tests:

```powershell
cd frontend
npm test
```

Run a frontend type check:

```powershell
cd frontend
npm run typecheck
```

The backend currently has no dedicated test command checked in. A basic smoke check is:

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then visit `http://127.0.0.1:8000/health`.

## Reports

Mission reports are generated by:

```text
POST /api/v1/reports/generate
```

with a JSON payload:

```json
{
  "simulation_id": "your_simulation_id"
}
```

Generated markdown files are written to:

```text
reports/generated/
```

## Documentation

- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [API Specification](docs/API_SPEC.md)
- [Digital Twin](docs/DIGITAL_TWIN.md)
- [Plugin System](docs/PLUGIN_SYSTEM.md)
- [AI/ML Strategy](docs/AI_ML_STRATEGY.md)
- [Realtime Pipeline](docs/REALTIME_PIPELINE.md)
- [TPS Engine](docs/TPS_ENGINE.md)
- [UI/UX System](docs/UI_UX_SYSTEM.md)
- [Cloud Roadmap](docs/CLOUD_ROADMAP.md)
- [MVP Roadmap](docs/MVP_ROADMAP.md)
