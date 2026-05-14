from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import ml, reports, simulations, telemetry, tps, visualization
from app.core.config import settings
from app.plugins.loader import load_plugins
from app.services.simulation_service import simulation_service

app = FastAPI(
    title="REGEN-TWIN Hypersonic API",
    version="0.1.0",
    description="Hackathon-ready REGEN-TWIN APIs for hypersonic TPS simulation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulations.router, prefix="/api/v1/simulations", tags=["simulations"])
app.include_router(tps.router, prefix="/api/v1/tps", tags=["tps"])
app.include_router(ml.router, prefix="/api/v1/ml", tags=["ml"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])
app.include_router(visualization.router, prefix="/api/v1/visualization", tags=["visualization"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


@app.on_event("startup")
async def startup() -> None:
    load_plugins(simulation_service.engine.plugin_registry)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "nominal", "system": "REGEN-TWIN"}
