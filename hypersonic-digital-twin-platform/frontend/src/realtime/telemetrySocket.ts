import type { TelemetryMessage } from "../state/types";

const WS_BASE = import.meta.env.VITE_WS_BASE ?? "ws://localhost:8000/api/v1";

export function connectTelemetry(simulationId: string, onMessage: (message: TelemetryMessage) => void) {
  const socket = new WebSocket(`${WS_BASE}/telemetry/ws?simulation_id=${simulationId}`);

  socket.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };

  socket.onopen = () => socket.send(JSON.stringify({ type: "client.ready", simulationId }));

  return () => socket.close();
}

