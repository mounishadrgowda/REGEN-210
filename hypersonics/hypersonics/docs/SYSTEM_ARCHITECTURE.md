# Complete System Architecture

## Product Framing

REGEN-TWIN is an AI-powered hypersonic digital twin platform focused on thermal protection systems. It presents like a national aerospace lab system while staying achievable for a student hackathon.

Core idea:

```text
Mission Controls -> API Gateway -> Digital Twin Orchestrator
                         |              |
                         |              +-> Physics Modules
                         |              +-> Plugin Modules
                         |              +-> ML Inference
                         |              +-> Report Generator
                         |
                         +-> WebSocket Telemetry Stream -> Live Dashboard
```

## Folder Structure

```text
hypersonic-digital-twin-platform/
  frontend/
    src/
      api/                  # REST client
      realtime/             # WebSocket client
      state/                # Digital twin UI state
      components/           # Dashboard and mission controls
      visualizations/       # 3D vehicle, heat maps, shockwave layers
  backend/
    app/
      api/v1/               # Versioned REST and WebSocket APIs
      core/                 # Settings, constants, app configuration
      schemas/              # Pydantic digital twin contracts
      services/             # Orchestration services
      realtime/             # WebSocket connection manager
      simulation/           # Engine and swappable physics modules
      plugins/              # Plugin registry and loader
      ml/                   # Inference adapters and model registry
  plugins/
    plasma_shielding/       # Example future subsystem
    adaptive_materials/     # Example future subsystem
  ml/
    models/                 # Versioned model cards and placeholder artifacts
    training/               # Training pipeline starter
  datasets/
    sample/                 # Demo telemetry
    schemas/                # JSON schemas for telemetry and training data
  configs/
    simulation.default.yaml # Default mission and material settings
    env.example             # Runtime environment variables
  reports/
    templates/              # Markdown/HTML report templates
  deployment/
    docker/                 # Docker Compose and Dockerfiles
    k8s/                    # Future cloud manifests
  docs/                     # Judge-facing and engineer-facing architecture
```

## Runtime Modules

| Module | Responsibility | Demo Status |
| --- | --- | --- |
| TPS Simulation | Heat flux, wall temp, material margin | Real simplified formulas |
| Aerothermal Estimator | Mach/altitude/geometry heating proxy | Real simplified formulas |
| Regenerative Cooling | Coolant heat absorption and efficiency | Real simplified formulas |
| Shockwave Visualization | Cone angle and flow overlay | Visual/simplified |
| Material Analysis | Material limit, density, sustainability | Real data table + scoring |
| Structural Risk | Risk from thermal margin and stress | Real heuristic |
| Mission Dashboard | Live run state, alerts, trends | Implement now |
| Telemetry | Streaming digital twin state | Implement now |
| Report Generation | Mission summary and risk matrix | Template now |

## Data Flow

1. User sets mission controls in the frontend.
2. Frontend posts `/api/v1/simulations/start`.
3. Backend creates a digital twin state and simulation session.
4. Simulation engine runs a tick loop.
5. Physics modules update slices of twin state.
6. ML adapters add predictions and recommendations.
7. Telemetry manager streams snapshots through WebSocket.
8. Frontend updates 3D vehicle, heatmap, charts, alerts, and report panels.

## What Wins Judges

- Show architecture as a digital twin, not just a calculator.
- Mention swappable physics modules and plugin registration.
- Use live telemetry and mission-state language.
- Keep formulas transparent and honest: "simplified hackathon surrogate."
- Visually separate real calculations from mocked AI predictions.
