import type { TelemetryMessage } from "../state/types";

function defaultWebSocketBase() {
  if (typeof window === "undefined") {
    return "ws://127.0.0.1:5173/api/v1";
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/v1`;
}

const WS_BASE = import.meta.env.VITE_WS_BASE ?? defaultWebSocketBase();

export function connectTelemetry(simulationId: string, onMessage: (message: TelemetryMessage) => void) {
  const socket = new WebSocket(`${WS_BASE}/telemetry/ws?simulation_id=${simulationId}`);

  socket.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };

  socket.onopen = () => socket.send(JSON.stringify({ type: "client.ready", simulationId }));

  return () => socket.close();
}
