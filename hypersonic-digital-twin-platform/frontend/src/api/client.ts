import type { SimulationStartRequest } from "../state/types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";

export async function startSimulation(payload: SimulationStartRequest) {
  const response = await fetch(`${API_BASE}/simulations/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Unable to start simulation");
  return response.json() as Promise<{ simulation_id: string; telemetry_ws: string }>;
}

export async function generateReport(simulationId: string) {
  const response = await fetch(`${API_BASE}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ simulation_id: simulationId }),
  });
  if (!response.ok) throw new Error("Unable to generate report");
  return response.json();
}

