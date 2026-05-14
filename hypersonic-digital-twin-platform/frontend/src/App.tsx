import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";
import { generateReport, startSimulation } from "./api/client";
import { IntelligenceRail } from "./components/IntelligenceRail";
import { MetricCard } from "./components/MetricCard";
import { MissionControls } from "./components/MissionControls";
import { connectTelemetry } from "./realtime/telemetrySocket";
import { defaultMission } from "./state/defaultMission";
import type { DigitalTwinState } from "./state/types";
import { TelemetryChart } from "./visualizations/TelemetryChart";
import { VehicleTwin } from "./visualizations/VehicleTwin";

export function App() {
  const [simulationId, setSimulationId] = useState<string>();
  const [state, setState] = useState<DigitalTwinState>();
  const [history, setHistory] = useState<DigitalTwinState[]>([]);
  const [reportStatus, setReportStatus] = useState("ready");

  const running = Boolean(simulationId);

  const metrics = useMemo(
    () => [
      { label: "Heat Flux", value: `${Math.round(state?.thermal.heat_flux_w_m2 ?? 0).toLocaleString()} W/m2`, tone: state?.risk.level },
      { label: "Wall Temp", value: `${Math.round(state?.thermal.max_surface_temp_k ?? 300)} K`, tone: state?.risk.level },
      { label: "Cooling", value: `${Math.round((state?.cooling.efficiency ?? 0) * 100)}%`, tone: "nominal" as const },
      { label: "Sustainability", value: `${Math.round((state?.sustainability.score ?? 0.72) * 100)}%`, tone: "nominal" as const },
    ],
    [state],
  );

  useEffect(() => {
    if (!simulationId) return;
    return connectTelemetry(simulationId, (message) => {
      setState(message.state);
      setHistory((items) => [...items.slice(-80), message.state]);
    });
  }, [simulationId]);

  async function handleStart() {
    const response = await startSimulation(defaultMission);
    setSimulationId(response.simulation_id);
  }

  async function handleReport() {
    if (!simulationId) return;
    setReportStatus("generating");
    const report = await generateReport(simulationId);
    setReportStatus(report.status);
  }

  return (
    <main className="app-shell">
      <header className="mission-bar">
        <div>
          <p className="eyebrow">AETHER-TWIN</p>
          <h1>Hypersonic TPS Digital Twin</h1>
        </div>
        <button className="export-action" onClick={handleReport}>
          <Download size={18} />
          {reportStatus === "ready" ? "Generate Report" : reportStatus}
        </button>
      </header>

      <div className="dashboard-grid">
        <MissionControls mission={defaultMission} running={running} onStart={handleStart} />

        <section className="mission-core">
          <div className="metric-grid">
            {metrics.map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone ?? "nominal"} />
            ))}
          </div>
          <VehicleTwin state={state} />
          <TelemetryChart history={history} />
        </section>

        <IntelligenceRail state={state} />
      </div>
    </main>
  );
}

