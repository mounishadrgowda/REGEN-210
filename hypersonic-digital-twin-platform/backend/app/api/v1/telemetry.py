from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.manager import telemetry_manager
from app.services.simulation_service import simulation_service

router = APIRouter()


@router.get("/latest")
async def latest() -> dict:
    state = simulation_service.latest()
    if state is None:
        return {"status": "idle", "state": None}
    return {"status": "nominal", "state": state.model_dump()}


@router.websocket("/ws")
async def telemetry_ws(websocket: WebSocket) -> None:
    await telemetry_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_manager.disconnect(websocket)

