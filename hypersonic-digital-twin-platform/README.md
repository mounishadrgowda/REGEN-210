# AETHER-TWIN: AI-Powered Hypersonic TPS Digital Twin

A prototype digital twin and thermal protection system platform for hypersonic vehicle simulation, telemetry, and AI-assisted decision support.

This repository contains:
- `backend/`: FastAPI backend, simulation engine, plugin loader, telemetry, ML API endpoints, and report scaffolding.
- `frontend/`: React + Vite dashboard with telemetry charts, status panels, and visualization components.
- `plugins/`: Optional subsystem extensions for adaptive materials, plasma shielding, and more.
- `ml/`: Model registry and training utilities.
- `datasets/`: Sample telemetry and schema definitions.
- `configs/`: Runtime and simulation configuration files.
- `deployment/`: Docker and Kubernetes starter deployment assets.

## Key Capabilities

- FastAPI backend with REST endpoints and WebSocket telemetry.
- TPS simulation endpoints for heat, risk, and system state.
- Modular plugin loader for material and shielding subsystems.
- Pydantic-based digital twin schemas for clean API contracts.
- Frontend dashboard starter with live telemetry integration.
- Ready-to-run Docker and Kubernetes manifests for deployment.

## Backend Dependencies

The backend is built on Python and requires the packages listed in `backend/requirements.txt`.

Core dependencies include:
- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings`
- `PyYAML`

## Quick Start

From the repository root:

```powershell
cd hypersonic-digital-twin-platform\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then start the frontend:

```powershell
cd ..\frontend
npm install
npm run dev
```

## Running the Backend

- API root: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Telemetry WebSocket: `ws://localhost:8000/api/v1/telemetry/ws`

## Development Notes

- Backend entrypoint: `backend/app/main.py`
- FastAPI routers are registered under `/api/v1`
- Plugin loader initializes at startup
- Configuration is driven by `backend/app/core/config.py`

## Project Structure

```text
hypersonic-digital-twin-platform/
  backend/                  # FastAPI backend and simulation services
  frontend/                 # React/Vite UI and dashboard
  plugins/                  # External subsystem plugins
  ml/                       # Model training and registry assets
  datasets/                 # Sample telemetry and schema definitions
  configs/                  # Simulation and runtime configuration
  deployment/               # Docker Compose and Kubernetes manifests
  docs/                     # Architecture and feature documentation
  reports/                  # Report templates and output assets
  scripts/                  # Helper automation scripts
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
