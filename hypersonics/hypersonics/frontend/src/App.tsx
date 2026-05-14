import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import { Check, Download, FileText } from "lucide-react";
import { generateReport, startSimulation } from "./api/client";
import { MissionControls } from "./components/MissionControls";
import { connectTelemetry } from "./realtime/telemetrySocket";
import { defaultMission } from "./state/defaultMission";
import type { DigitalTwinState, MissionReport, RiskLevel, SimulationStartRequest } from "./state/types";
import { SystemComponentsView } from "./visualizations/SystemComponentsView";
import { ThreeDesignView } from "./visualizations/ThreeDesignView";
import { TelemetryChart } from "./visualizations/TelemetryChart";
import { VehicleDiagramView } from "./visualizations/VehicleDiagramView";

interface DerivedTelemetry {
  altitudeKm: number;
  coolingDeltaK: number;
  dragForceKn: number;
  dynamicPressureKpa: number;
  fuelFlowKgS: number;
  heatFluxMwM2: number;
  liveMach: number;
  passengerRisk: string;
  peakHeatFluxMwM2: number;
  realGasEffects: string;
  structuralIntegrity: number;
  surfaceTempC: number;
  surfaceTempK: number;
  thermalLoadMw: number;
  thermalStressMpa: number;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function densityAtAltitude(altitudeM: number) {
  return 1.225 * Math.exp(-altitudeM / 8500);
}

function materialLabel(materialId: string) {
  const labels: Record<string, string> = {
    c_phenolic: "C-Phenolic Ablator",
    reinforced_carbon_carbon: "Reinforced Carbon-Carbon",
    bio_ceramic_composite: "Bio Ceramic Composite",
  };
  return labels[materialId] ?? materialId.replaceAll("_", " ");
}

function passengerRisk(level?: RiskLevel) {
  if (level === "critical") return "HIGH";
  if (level === "guarded") return "MED";
  return "LOW";
}

function machRegime(mach: number) {
  if (mach >= 8) return "HYPERSONIC";
  if (mach >= 5) return "ENTRY HYPERSONIC";
  return "SUPERSONIC";
}

function buildTelemetry(mission: SimulationStartRequest, state?: DigitalTwinState, history: DigitalTwinState[] = []): DerivedTelemetry {
  const liveMach = state?.aircraft.mach ?? mission.initial_conditions.mach;
  const altitudeM = state?.aircraft.altitude_m ?? mission.initial_conditions.altitude_m;
  const velocityMps = state?.aircraft.velocity_m_s ?? liveMach * 295;
  const density = state?.aerodynamic.density_kg_m3 ?? densityAtAltitude(altitudeM);
  const dynamicPressurePa = state?.aerodynamic.dynamic_pressure_pa ?? 0.5 * density * velocityMps ** 2;
  const dragForceN = dynamicPressurePa * mission.vehicle.reference_area_m2 * mission.vehicle.drag_coefficient;
  const fuelFlowKgS = Math.max(0, (dragForceN * velocityMps) / (43_000_000 * 0.4));
  const heatFluxWm2 = state?.thermal.heat_flux_w_m2 ?? 1_050_000;
  const heatRemovedWm2 = state?.cooling.heat_removed_w_m2 ?? mission.cooling.mass_flow_kg_s * 14300 * 120 / mission.tps.surface_area_m2;
  const thermalMargin = state?.thermal.thermal_margin ?? 1;
  const structuralMargin = 1 - (state?.structural?.failure_probability ?? 0);
  const surfaceTempK = state?.thermal.max_surface_temp_k ?? 300;
  const peakHeatFluxWm2 = Math.max(heatFluxWm2, ...history.map((item) => item.thermal.heat_flux_w_m2));
  const coolingDeltaK = mission.cooling.mass_flow_kg_s > 0 ? -(heatRemovedWm2 * mission.tps.surface_area_m2) / (mission.cooling.mass_flow_kg_s * 14300) : 0;

  return {
    altitudeKm: altitudeM / 1000,
    coolingDeltaK,
    dragForceKn: dragForceN / 1000,
    dynamicPressureKpa: dynamicPressurePa / 1000,
    fuelFlowKgS,
    heatFluxMwM2: heatFluxWm2 / 1_000_000,
    liveMach,
    passengerRisk: passengerRisk(state?.risk.level),
    peakHeatFluxMwM2: peakHeatFluxWm2 / 1_000_000,
    realGasEffects: liveMach >= 8 ? "HIGH" : liveMach >= 6 ? "MODERATE" : "LOW",
    structuralIntegrity: clamp(Math.min(thermalMargin, structuralMargin) * 100, 0, 100),
    surfaceTempC: surfaceTempK - 273.15,
    surfaceTempK,
    thermalLoadMw: (heatRemovedWm2 * mission.tps.surface_area_m2) / 1_000_000,
    thermalStressMpa: -Math.round((surfaceTempK - 273) * 0.72 + Math.max(0, liveMach - 5) * 38),
  };
}

function StatusTile({ label, value }: { label: string; value: string }) {
  return (
    <section className="status-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}

function TelemetryStat({ accent, label, value, detail }: { accent: string; label: string; value: string; detail?: string }) {
  return (
    <section className="telemetry-stat" style={{ "--accent": accent } as CSSProperties}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </section>
  );
}

function TpsStatusPanel({ mission, telemetry, riskLevel }: { mission: SimulationStartRequest; telemetry: DerivedTelemetry; riskLevel?: RiskLevel }) {
  const safe = riskLevel !== "critical" && telemetry.structuralIntegrity >= 55;
  return (
    <section className={`tps-status ${safe ? "safe" : "warning"}`}>
      <h2>
        <Check size={18} />
        TPS {safe ? "WITHIN SAFE LIMITS" : "REQUIRES ACTIVE CONTROL"}
      </h2>
      <div className="terminal-lines">
        <p>Mach {telemetry.liveMach.toFixed(2)} at {telemetry.altitudeKm.toFixed(1)} km altitude.</p>
        <p>Surface Temperature: {Math.round(telemetry.surfaceTempK)} K</p>
        <p>Peak Heat Flux: {telemetry.peakHeatFluxMwM2.toFixed(2)} MW/m2</p>
        <p>Material: {materialLabel(mission.tps.material_id)}</p>
        <p>Real Gas Effects: {telemetry.realGasEffects}</p>
        <p>Thermal Stress: {telemetry.thermalStressMpa} MPa</p>
        <p>Regen cooling active - removing {telemetry.thermalLoadMw.toFixed(2)} MW thermal load.</p>
      </div>
    </section>
  );
}

function EngineeringFindings({ mission, telemetry }: { mission: SimulationStartRequest; telemetry: DerivedTelemetry }) {
  const cruiseMinutes = telemetry.fuelFlowKgS > 0 ? 1000 / telemetry.fuelFlowKgS / 60 : 0;
  const heatVerdict = telemetry.structuralIntegrity > 65 ? "Within TPS margins." : "TPS margin narrowing.";

  return (
    <section className="findings">
      <div className="section-title">
        <span />
        <p>Engineering Findings</p>
      </div>
      <article>
        <b>HEAT FLUX:</b> Stagnation q={telemetry.peakHeatFluxMwM2.toFixed(3)} MW/m2 at Rn={mission.vehicle.nose_radius_m.toFixed(2)} m. {heatVerdict}
      </article>
      <article>
        <b>PROPULSION:</b> m_dot={telemetry.fuelFlowKgS.toFixed(4)} kg/s sustains {telemetry.dragForceKn.toFixed(2)} kN drag. 1000 kg fuel -&gt; ~{cruiseMinutes.toFixed(1)} min cruise. eta=0.4, LHV=43 MJ/kg.
      </article>
      <article className="purple">
        <b>SCRAMJET REGIME:</b> Mach {telemetry.liveMach.toFixed(2)} enables supersonic combustion. Real-gas dissociation significant above Mach 8.
      </article>
    </section>
  );
}

function SubsystemPanel({ state }: { state?: DigitalTwinState }) {
  const plasmaReduction = (state?.plasma_shielding?.reduction_factor ?? 0) * 100;
  const rpicReduction = (state?.rpic?.heat_flux_reduction ?? 0) * 100;
  const rpicDensity = state?.rpic?.plasma_density_m3 ?? 0;
  const zonal = state?.zonal_cooling;
  const zones = zonal?.zones ?? [];
  const structural = state?.structural;
  const ai = state?.ai;

  return (
    <section className="subsystem-grid">
      <article className="subsystem-panel">
        <span>Plasma Shielding</span>
        <strong>{plasmaReduction.toFixed(1)}%</strong>
        <p>
          {state?.plasma_shielding ? `${(state.plasma_shielding.heat_flux_after_w_m2 / 1_000_000).toFixed(3)} MW/m2 exposed flux` : "Waiting for simulation"}
        </p>
        <p>
          B {(state?.plasma_shielding?.magnetic_field_t ?? 0).toFixed(1)} T | Hall {(state?.plasma_shielding?.hall_parameter ?? 0).toFixed(2)} | Power{" "}
          {(state?.plasma_shielding?.power_draw_kw ?? 0).toFixed(0)} kW
        </p>
      </article>

      <article className="subsystem-panel">
        <span>RPIC Control</span>
        <strong>{rpicReduction.toFixed(1)}%</strong>
        <p>
          Effort {(state?.rpic?.control_effort ?? 0).toFixed(2)} | Density {rpicDensity.toExponential(2)} m-3 | Power {(state?.rpic?.power_draw_kw ?? 0).toFixed(0)} kW
        </p>
        <p>B-field {(state?.rpic?.magnetic_field_t ?? 0).toFixed(1)} T boosts plasma authority with saturation.</p>
      </article>

      <article className="subsystem-panel zones">
        <span>Zonal Cooling</span>
        <strong>{zonal?.active_zone ?? "standby"}</strong>
        <p>
          Max zone {Math.round(zonal?.max_zone_temp_k ?? 300)} K | Min margin {((zonal?.min_zone_margin ?? 1) * 100).toFixed(1)}%
        </p>
        <div className="zone-list">
          {zones.length === 0 ? (
            <small>No live zone samples</small>
          ) : (
            zones.map((zone) => (
              <small key={zone.name}>
                {zone.name.replaceAll("_", " ")}: {Math.round(zone.surface_temp_k)} K, {(zone.efficiency * 100).toFixed(0)}%
              </small>
            ))
          )}
        </div>
      </article>

      <article className="subsystem-panel">
        <span>ML Failure Model</span>
        <strong>{((ai?.failure_probability ?? 0) * 100).toFixed(1)}%</strong>
        <p>
          {ai?.model_stage ?? "surrogate standby"} | Confidence {((ai?.model_confidence ?? 0) * 100).toFixed(0)}% | RUL{" "}
          {ai?.maintenance_remaining_cycles ?? structural?.remaining_life_cycles ?? 120} cycles
        </p>
        <p>
          Stress {(structural?.joint_stress_mpa ?? 0).toFixed(0)} MPa | Fatigue {((structural?.fatigue_damage ?? 0) * 100).toFixed(2)}%
        </p>
      </article>
    </section>
  );
}

export function App() {
  const [mission, setMission] = useState<SimulationStartRequest>(defaultMission);
  const [simulationId, setSimulationId] = useState<string>();
  const [state, setState] = useState<DigitalTwinState>();
  const [history, setHistory] = useState<DigitalTwinState[]>([]);
  const [reportStatus, setReportStatus] = useState("ready");
  const [report, setReport] = useState<MissionReport>();
  const [activeTab, setActiveTab] = useState<"dashboard" | "design" | "diagram" | "components">("dashboard");

  const running = Boolean(simulationId);
  const telemetry = useMemo(() => buildTelemetry(mission, state, history), [history, mission, state]);

  useEffect(() => {
    if (!simulationId) return;
    return connectTelemetry(simulationId, (message) => {
      setState(message.state);
      setHistory((items) => [...items.slice(-120), message.state]);
    });
  }, [simulationId]);

  async function handleStart() {
    setReport(undefined);
    setReportStatus("ready");
    const response = await startSimulation(mission);
    setSimulationId(response.simulation_id);
  }

  function handleMissionChange(nextMission: SimulationStartRequest) {
    setMission(nextMission);
    setReport(undefined);
    setReportStatus("ready");
  }

  function handleReset() {
    setMission(defaultMission);
    setState(undefined);
    setHistory([]);
    setSimulationId(undefined);
    setReportStatus("ready");
    setReport(undefined);
  }

  async function handleReport() {
    if (!simulationId) return;
    setReportStatus("generating");
    try {
      const generatedReport = await generateReport(simulationId);
      setReport(generatedReport);
      setReportStatus(generatedReport.status);
    } catch {
      setReportStatus("error");
    }
  }

  function handleDownloadReport() {
    if (!report) return;
    const url = URL.createObjectURL(new Blob([report.markdown], { type: "text/markdown;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = report.download_filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="app-shell">
      <header className="mission-bar">
        <div>
          <p className="eyebrow">REGEN-TWIN</p>
          <h1>Hypersonic Regenerative TPS Console</h1>
        </div>
        <nav className="view-tabs" aria-label="Primary views">
          <button className={activeTab === "dashboard" ? "active" : ""} onClick={() => setActiveTab("dashboard")}>
            Dashboard
          </button>
          <button className={activeTab === "design" ? "active" : ""} onClick={() => setActiveTab("design")}>
            3D Design
          </button>
          <button className={activeTab === "diagram" ? "active" : ""} onClick={() => setActiveTab("diagram")}>
            Vehicle Diagram
          </button>
          <button className={activeTab === "components" ? "active" : ""} onClick={() => setActiveTab("components")}>
            System Components
          </button>
        </nav>
        {activeTab === "dashboard" && (
          <button className="export-action" onClick={handleReport} disabled={!simulationId || reportStatus === "generating"}>
            <Download size={18} />
            {!simulationId ? "Start Mission First" : reportStatus === "ready" ? "Generate Report" : reportStatus}
          </button>
        )}
      </header>

      {activeTab === "dashboard" ? (
        <div className="dashboard-grid">
          <MissionControls mission={mission} running={running} state={state} onStart={handleStart} onMissionChange={handleMissionChange} onReset={handleReset} />

          <section className="mission-core">
            <div className="status-grid">
              <StatusTile label="Mach" value={telemetry.liveMach.toFixed(2)} />
              <StatusTile label="Dynamic Pressure" value={`${telemetry.dynamicPressureKpa.toFixed(1)} KPA`} />
              <StatusTile label="Structural Integrity" value={`${telemetry.structuralIntegrity.toFixed(1)}%`} />
              <StatusTile label="Passenger Risk" value={telemetry.passengerRisk} />
            </div>

            <EngineeringFindings mission={mission} telemetry={telemetry} />
            <TpsStatusPanel mission={mission} telemetry={telemetry} riskLevel={state?.risk.level} />
            <SubsystemPanel state={state} />

            <div className="telemetry-grid">
              <TelemetryStat accent="#34b7df" label="Surface Temp" value={`${Math.round(telemetry.surfaceTempK)} K`} detail={`${Math.round(telemetry.surfaceTempC)} C`} />
              <TelemetryStat accent="#d86d1d" label="Heat Flux" value={`${telemetry.heatFluxMwM2.toFixed(3)} MW/m2`} detail={`net ${((state?.thermal.net_heat_flux_w_m2 ?? 0) / 1_000_000).toFixed(3)} MW/m2`} />
              <TelemetryStat accent="#56bce3" label="Drag Force" value={`${telemetry.dragForceKn.toFixed(2)} kN`} />
              <TelemetryStat accent="#2e963f" label="Fuel Flow" value={`${telemetry.fuelFlowKgS.toFixed(4)} kg/s`} />
              <TelemetryStat accent="#252525" label="Air Density" value={`${(state?.aerodynamic.density_kg_m3 ?? densityAtAltitude(mission.initial_conditions.altitude_m)).toExponential(3)} kg/m3`} />
              <TelemetryStat accent="#2e963f" label="Cooling dT" value={`${Math.round(telemetry.coolingDeltaK)} K`} />
              <TelemetryStat accent="#a9452d" label="Mach Regime" value={`M${telemetry.liveMach.toFixed(2)} ${machRegime(telemetry.liveMach)}`} />
            </div>

            <TelemetryChart history={history} mission={mission} />

            {report && (
              <section className={`report-panel ${report.risk.level}`}>
                <div className="report-head">
                  <div>
                    <p className="eyebrow">Mission Report</p>
                    <h2>{report.report_id}</h2>
                  </div>
                  <button className="secondary-action" onClick={handleDownloadReport}>
                    <FileText size={18} />
                    Download Markdown
                  </button>
                </div>

                <p className="report-assessment">{report.executive_summary.assessment}</p>

                <div className="report-grid">
                  <span>
                    Judge Score
                    <strong>{report.scorecard.overall}/100</strong>
                  </span>
                  <span>
                    Peak Heat
                    <strong>{report.thermal.peak_heat_flux_mw_m2} MW/m2</strong>
                  </span>
                  <span>
                    ML Confidence
                    <strong>{report.intelligence.model_confidence_pct}%</strong>
                  </span>
                  <span>
                    RUL
                    <strong>{report.structural.remaining_life_cycles} cycles</strong>
                  </span>
                </div>

                <div className="report-recommendations">
                  <span>Judge Highlights</span>
                  {report.judge_highlights.slice(0, 4).map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
              </section>
            )}
          </section>
        </div>
      ) : activeTab === "design" ? (
        <ThreeDesignView mission={mission} state={state} />
      ) : activeTab === "diagram" ? (
        <VehicleDiagramView mission={mission} state={state} onApplyDesign={setMission} />
      ) : (
        <SystemComponentsView mission={mission} state={state} />
      )}
    </main>
  );
}
