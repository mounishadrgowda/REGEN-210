import json
from typing import Any

from fastapi import WebSocket


class TelemetryConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        encoded = json.dumps(message)
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(encoded)
            except RuntimeError:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)


telemetry_manager = TelemetryConnectionManager()

