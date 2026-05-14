import { useEffect, useMemo, useState } from "react";
import { Check, RefreshCw } from "lucide-react";
import { generateVehicleDesign } from "../api/client";
import type { DesignComponent, DesignGeneratorResponse, DigitalTwinState, SimulationStartRequest } from "../state/types";

interface VehicleDiagramViewProps {
  mission: SimulationStartRequest;
  state?: DigitalTwinState;
  onApplyDesign: (mission: SimulationStartRequest) => void;
}

const labelOffsets: Record<string, { dx: number; dy: number; anchor: "start" | "end" }> = {
  bow_shock: { dx: -7, dy: -17, anchor: "end" },
  nose: { dx: -8, dy: -12, anchor: "end" },
  tps: { dx: -7, dy: -11, anchor: "end" },
  rpic: { dx: 6, dy: -14, anchor: "start" },
  cooling: { dx: 7, dy: -8, anchor: "start" },
  scramjet: { dx: 8, dy: -10, anchor: "start" },
  nozzle: { dx: 5, dy: -8, anchor: "start" },
};

function statValue(value?: number, suffix = "") {
  if (value === undefined || Number.isNaN(value)) return "--";
  return `${value.toFixed(1)}${suffix}`;
}

function annotationLabel(component: DesignComponent) {
  return component.name.length > 20 ? component.name.slice(0, 20) : component.name;
}

function VehicleDiagramSvg({ design, onSelect }: { design?: DesignGeneratorResponse; onSelect: (component: DesignComponent) => void }) {
  const components = design?.components ?? [];

  return (
    <svg className="vehicle-diagram-svg" viewBox="0 0 100 58" role="img" aria-label="Annotated hypersonic vehicle diagram">
      <defs>
        <pattern id="diagramGrid" width="5" height="5" patternUnits="userSpaceOnUse">
          <path d="M 5 0 L 0 0 0 5" fill="none" stroke="rgba(80, 240, 210, 0.16)" strokeWidth="0.16" />
        </pattern>
        <linearGradient id="fuselageGlass" x1="0" x2="1">
          <stop offset="0" stopColor="#1cd4d9" stopOpacity="0.22" />
          <stop offset="1" stopColor="#38ff9c" stopOpacity="0.13" />
        </linearGradient>
        <linearGradient id="thermalNose" x1="0" x2="1">
          <stop offset="0" stopColor="#ff452f" stopOpacity="0.55" />
          <stop offset="1" stopColor="#ff9a1f" stopOpacity="0.08" />
        </linearGradient>
      </defs>

      <rect x="0" y="0" width="100" height="58" fill="#151912" />
      <rect x="0" y="0" width="100" height="58" fill="url(#diagramGrid)" />
      {[10, 20, 30, 40, 50].map((y) => (
        <line key={y} x1="0" x2="100" y1={y} y2={y} stroke="#0de0d0" strokeDasharray="0.7 1.4" strokeOpacity="0.16" />
      ))}

      <path d="M2 35 L15 29 L2 23" fill="none" stroke="#d96922" strokeWidth="0.2" strokeDasharray="1.3 1.2" opacity="0.72" />
      <path d="M15 29 C23 20, 34 20, 44 23 C56 27, 70 25, 91 22" fill="none" stroke="#e2b11e" strokeWidth="0.35" opacity="0.58" />
      <path d="M15 29 C23 38, 38 41, 52 39 C67 36, 78 36, 91 38" fill="none" stroke="#e2b11e" strokeWidth="0.35" opacity="0.58" />

      <polygon points="15,29 21,25 24,26.3 25.4,31.5 24,36.4 21,37.6" fill="url(#thermalNose)" stroke="#ff5f3b" strokeWidth="0.3" opacity="0.76" />
      <polygon points="27,24.8 51,23.7 84,25.1 84,38.5 48.5,38 27.2,35.5" fill="url(#fuselageGlass)" stroke="#22e0dc" strokeWidth="0.35" opacity="0.85" />
      <polygon points="49,22.8 56,15.4 85.8,25.3 49.2,27.1" fill="#00d872" opacity="0.18" stroke="#00f18a" strokeWidth="0.35" />
      <polygon points="49.2,38.1 56.9,48.6 85.2,38.7 49.1,35.8" fill="#00d872" opacity="0.18" stroke="#00f18a" strokeWidth="0.35" />
      <polygon points="35.2,37.1 61.3,37.6 65.1,45.2 48.5,44.8 37.8,41.2" fill="#f4a51e" opacity="0.18" stroke="#ffb12a" strokeWidth="0.3" />
      <rect x="68" y="27.4" width="16" height="11" fill="#db7332" opacity="0.18" stroke="#ff7f2a" strokeWidth="0.3" />
      <polygon points="84,28.8 91,26.1 94.6,29.2 94.6,35.8 91,38.7 84,36.4" fill="#a65cff" opacity="0.2" stroke="#a65cff" strokeWidth="0.35" />
      <line x1="95" x2="95" y1="22.5" y2="42" stroke="#a65cff" strokeWidth="0.45" />

      <path d="M34.8 25 C42 24.5 52 24.1 61 24.4" stroke="#00e8aa" strokeWidth="0.55" opacity="0.5" />
      <path d="M27 29.5 C43 28.3 59 28.2 84 29.1" stroke="#18d7f3" strokeWidth="0.45" opacity="0.5" />
      <path d="M27 31.4 C43 31.1 59 31.4 84 32.2" stroke="#18d7f3" strokeWidth="0.35" strokeDasharray="1 1" opacity="0.42" />

      {components.map((component) => {
        const offset = labelOffsets[component.id] ?? { dx: 5, dy: -8, anchor: "start" as const };
        const labelX = component.x + offset.dx;
        const labelY = component.y + offset.dy;
        return (
          <g key={component.id} className="diagram-node" tabIndex={0} onClick={() => onSelect(component)} onKeyDown={(event) => event.key === "Enter" && onSelect(component)}>
            <line x1={component.x} y1={component.y} x2={labelX} y2={labelY + 1} stroke={component.color} strokeDasharray="1 1" strokeWidth="0.35" opacity="0.9" />
            <circle cx={component.x} cy={component.y} r="0.75" fill={component.color} />
            <text x={labelX} y={labelY} fill={component.color} textAnchor={offset.anchor} className="diagram-label">
              {annotationLabel(component)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function VehicleDiagramView({ mission, state, onApplyDesign }: VehicleDiagramViewProps) {
  const [design, setDesign] = useState<DesignGeneratorResponse>();
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [selectedComponent, setSelectedComponent] = useState<DesignComponent>();

  const missionKey = useMemo(
    () =>
      JSON.stringify({
        vehicle: mission.vehicle,
        initial_conditions: mission.initial_conditions,
        tps: mission.tps,
        cooling: mission.cooling,
      }),
    [mission],
  );

  async function loadDesign() {
    setStatus("loading");
    try {
      const generated = await generateVehicleDesign(mission);
      setDesign(generated);
      setSelectedComponent(generated.components[0]);
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }

  useEffect(() => {
    loadDesign();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [missionKey]);

  function applyDesign() {
    if (!design) return;
    onApplyDesign({
      ...mission,
      vehicle: design.mission_patch.vehicle,
      tps: design.mission_patch.tps,
      cooling: design.mission_patch.cooling,
    });
  }

  return (
    <section className="vehicle-diagram-page">
      <div className="diagram-command-bar">
        <div>
          <p className="eyebrow">Vehicle Diagram</p>
          <h2>{design?.name ?? "Generating Hypersonic Design"}</h2>
        </div>
        <button className="secondary-action" onClick={loadDesign} disabled={status === "loading"}>
          <RefreshCw size={18} />
          {status === "loading" ? "Generating" : "Regenerate"}
        </button>
        <button className="primary-action" onClick={applyDesign} disabled={!design}>
          <Check size={18} />
          Apply Design
        </button>
      </div>

      <div className="diagram-stat-grid">
        <section>
          <span>Heat Reduction</span>
          <strong>{statValue(design?.predicted.heat_reduction_pct, "%")}</strong>
        </section>
        <section>
          <span>Optimized Heat Flux</span>
          <strong>{design ? `${(design.predicted.optimized_heat_flux_w_m2 / 1_000_000).toFixed(3)} MW/m2` : "--"}</strong>
        </section>
        <section>
          <span>Thermal Margin</span>
          <strong>{design ? `${(design.predicted.thermal_margin * 100).toFixed(1)}%` : "--"}</strong>
        </section>
        <section>
          <span>Model</span>
          <strong>{design?.model_stage ?? "standby"}</strong>
        </section>
      </div>

      <div className="vehicle-diagram-board">
        <VehicleDiagramSvg design={design} onSelect={setSelectedComponent} />
      </div>

      <div className="diagram-detail-grid">
        <article className="diagram-feature">
          <span>Generated Geometry</span>
          <strong>Ogival Delta Waverider</strong>
          <p>
            Nose {design?.geometry.nose_radius_m.toFixed(2) ?? "--"} m | LE radius {design?.geometry.leading_edge_radius_mm.toFixed(1) ?? "--"} mm | Sweep{" "}
            {design?.geometry.wing_sweep_deg ?? "--"} deg | L/D {design?.predicted.lift_to_drag.toFixed(2) ?? "--"}
          </p>
        </article>

        <article className="diagram-feature">
          <span>Thermal Stack</span>
          <strong>{design?.materials.nose ?? "UHTC + carbon-carbon"}</strong>
          <p>
            {design?.materials.leading_edges ?? "Leading-edge cap"} | {design?.materials.skin ?? "Acreage TPS"} | Coolant {design?.materials.coolant ?? mission.cooling.coolant}
          </p>
        </article>

        <article className="diagram-feature">
          <span>Live Comparison</span>
          <strong>{state ? `${((state.thermal.heat_flux_w_m2 || 0) / 1_000_000).toFixed(3)} MW/m2` : "No stream"}</strong>
          <p>
            Generated baseline {design ? `${(design.predicted.baseline_heat_flux_w_m2 / 1_000_000).toFixed(3)} MW/m2` : "--"} | Cooling power{" "}
            {design?.predicted.cooling_power_kw.toFixed(0) ?? "--"} kW
          </p>
        </article>

        <article className="diagram-feature">
          <span>Selected Component</span>
          <strong>{selectedComponent?.name ?? "Click a node"}</strong>
          <p>
            {selectedComponent
              ? `${selectedComponent.role} | ${selectedComponent.temp_k} K | ${selectedComponent.status}`
              : "Select any labeled node on the vehicle diagram for a focused engineering note."}
          </p>
        </article>
      </div>

      <div className="component-strip">
        {(design?.components ?? []).map((component) => (
          <article key={component.id}>
            <span style={{ backgroundColor: component.color }} />
            <div>
              <b>{component.name}</b>
              <small>
                {component.role} | {component.temp_k} K | {component.status}
              </small>
            </div>
          </article>
        ))}
      </div>

      {status === "error" && <p className="diagram-error">Design generator is offline.</p>}
    </section>
  );
}
