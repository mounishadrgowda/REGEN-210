import type { CSSProperties } from "react";
import type { DigitalTwinState, SimulationStartRequest } from "../state/types";

interface SystemComponentsViewProps {
  mission: SimulationStartRequest;
  state?: DigitalTwinState;
}

interface ComponentCardData {
  accent: string;
  category: string;
  title: string;
  status: string;
  specs: Array<[string, string]>;
  note: string;
}

function materialLabel(materialId: string) {
  const labels: Record<string, string> = {
    c_phenolic: "Carbon Phenolic",
    reinforced_carbon_carbon: "Reinforced Carbon-Carbon",
    ultra_high_temp_ceramic: "ZrB2-SiC UHTC",
    bio_ceramic_composite: "Bio Ceramic Composite",
  };
  return labels[materialId] ?? materialId.replaceAll("_", " ");
}

function formatNumber(value: number | undefined, digits = 1) {
  if (value === undefined || Number.isNaN(value)) return "--";
  return value.toFixed(digits);
}

function buildCards(mission: SimulationStartRequest, state?: DigitalTwinState): ComponentCardData[] {
  const mach = state?.aircraft.mach ?? mission.initial_conditions.mach;
  const heatFluxMw = (state?.thermal.heat_flux_w_m2 ?? 0) / 1_000_000;
  const netHeatFluxMw = (state?.thermal.net_heat_flux_w_m2 ?? 0) / 1_000_000;
  const dynamicPressureKpa = (state?.aerodynamic.dynamic_pressure_pa ?? 0) / 1000;
  const stagnationTemp = state?.aerodynamic.stagnation_temperature_k ?? 0;
  const coolingEfficiency = (state?.cooling.efficiency ?? 0) * 100;
  const plasmaReduction = (state?.plasma_shielding.reduction_factor ?? 0) * 100;
  const rpicReduction = (state?.rpic.heat_flux_reduction ?? 0) * 100;
  const structural = state?.structural;
  const ai = state?.ai;

  return [
    {
      accent: "#ff4d4d",
      title: "UHTC Nose Cone",
      category: "Thermal Protection - Nose",
      status: state?.risk.level ?? "standby",
      specs: [
        ["Material", materialLabel(mission.tps.material_id)],
        ["Nose Radius", `${mission.vehicle.nose_radius_m.toFixed(2)} m`],
        ["Heat Flux", `${formatNumber(heatFluxMw, 3)} MW/m2`],
        ["Stagnation Temp", `${formatNumber(stagnationTemp, 0)} K`],
        ["Thermal Margin", `${formatNumber((state?.thermal.thermal_margin ?? 1) * 100, 1)}%`],
      ],
      note: "Blunter ogival radius reduces stagnation heating while the active TPS stack absorbs residual nose and shoulder loads.",
    },
    {
      accent: "#ff9500",
      title: "TPS Tile Array",
      category: "Thermal Protection - Body",
      status: state ? "active" : "configured",
      specs: [
        ["Thickness", `${mission.tps.thickness_mm.toFixed(1)} mm`],
        ["Surface Area", `${mission.tps.surface_area_m2.toFixed(1)} m2`],
        ["Net Heat Flux", `${formatNumber(netHeatFluxMw, 3)} MW/m2`],
        ["Thermal Load", `${formatNumber(state?.thermal.thermal_load_mj_m2, 2)} MJ/m2`],
        ["Peak Surface", `${formatNumber(state?.thermal.max_surface_temp_k, 0)} K`],
      ],
      note: "Acreage tiles are evaluated against net heat flux after plasma, RPIC, regenerative cooling, and zonal redistribution.",
    },
    {
      accent: "#ff6b2a",
      title: "Variable-Geometry Scramjet",
      category: "Propulsion - Hypersonic Core",
      status: mach >= 5 ? "lit" : "standby",
      specs: [
        ["Regime", `Mach ${mach.toFixed(2)}`],
        ["Dynamic Pressure", `${formatNumber(dynamicPressureKpa, 1)} kPa`],
        ["Drag Coeff.", mission.vehicle.drag_coefficient.toFixed(2)],
        ["Reference Area", `${mission.vehicle.reference_area_m2.toFixed(1)} m2`],
        ["Phase", state?.aircraft.flight_phase ?? "pre-run"],
      ],
      note: "The propulsion model is tied to vehicle drag and dynamic pressure so fuel-flow estimates move with the actual flight envelope.",
    },
    {
      accent: "#00d9a6",
      title: "Zonal Regen Cooling",
      category: "Thermal Management - Active",
      status: state?.zonal_cooling.active_zone ?? "standby",
      specs: [
        ["Coolant", mission.cooling.coolant.replaceAll("_", " ")],
        ["Mass Flow", `${mission.cooling.mass_flow_kg_s.toFixed(2)} kg/s`],
        ["Efficiency", `${formatNumber(coolingEfficiency, 1)}%`],
        ["Active Zone", state?.zonal_cooling.active_zone ?? "--"],
        ["Balance", `${formatNumber((state?.zonal_cooling.balance_quality ?? 0) * 100, 1)}%`],
      ],
      note: "Flow is summarized by zone so leading-edge and nose thermal constraints can be managed separately from body acreage tiles.",
    },
    {
      accent: "#a65cff",
      title: "RPIC Plasma Controller",
      category: "MHD Boundary Control",
      status: state?.rpic.enabled ? "active" : "standby",
      specs: [
        ["Heat Reduction", `${formatNumber(rpicReduction, 1)}%`],
        ["Control Effort", `${formatNumber((state?.rpic.control_effort ?? 0) * 100, 1)}%`],
        ["Ionization", `${formatNumber((state?.rpic.ionization_fraction ?? 0) * 100, 1)}%`],
        ["Power Draw", `${formatNumber(state?.rpic.power_draw_kw, 0)} kW`],
        ["Density", `${(state?.rpic.plasma_density_m3 ?? 0).toExponential(2)} m-3`],
      ],
      note: "RPIC acts as a prize-ready research hook: a controllable plasma layer that reduces exposed heat before cooling is applied.",
    },
    {
      accent: "#12d8f0",
      title: "Plasma Shielding",
      category: "Thermal Modifier - Sheath",
      status: state?.plasma_shielding.enabled ? "active" : "standby",
      specs: [
        ["Reduction", `${formatNumber(plasmaReduction, 1)}%`],
        ["Before", `${formatNumber((state?.plasma_shielding.heat_flux_before_w_m2 ?? 0) / 1_000_000, 3)} MW/m2`],
        ["After", `${formatNumber((state?.plasma_shielding.heat_flux_after_w_m2 ?? 0) / 1_000_000, 3)} MW/m2`],
        ["Mach Link", mach >= 5 ? "engaged" : "armed"],
        ["Phase", "post-thermal"],
      ],
      note: "This module records pre/post heat-flux values so judges can see the shielding contribution rather than only a final number.",
    },
    {
      accent: "#06d878",
      title: "Ogival Delta Wings",
      category: "Aerodynamics - Lift & Control",
      status: "swept",
      specs: [
        ["Geometry", "ogival delta"],
        ["Sweep Target", "~74 deg"],
        ["AoA", `${mission.initial_conditions.angle_of_attack_deg.toFixed(1)} deg`],
        ["Shock Cone", `${formatNumber(state?.aerodynamic.shock_cone_angle_deg, 2)} deg`],
        ["Density", `${(state?.aerodynamic.density_kg_m3 ?? 0).toExponential(2)} kg/m3`],
      ],
      note: "The wing planform spreads leading-edge heating and keeps lift/drag coupled to the simulation state.",
    },
    {
      accent: "#1bb5ff",
      title: "Avionics & Sensor Bay",
      category: "Telemetry - Active Array",
      status: ai?.model_stage ?? "standby",
      specs: [
        ["ML Stage", ai?.model_stage ?? "--"],
        ["Confidence", `${formatNumber((ai?.model_confidence ?? 0) * 100, 1)}%`],
        ["Anomaly", `${formatNumber((ai?.anomaly_score ?? 0) * 100, 1)}%`],
        ["Heatmap", `${ai?.spatial_heatmap_k.length ?? 0} x ${ai?.spatial_heatmap_k[0]?.length ?? 0}`],
        ["Forecast", `${ai?.heat_forecast_k[ai.heat_forecast_k.length - 1] ?? "--"} K`],
      ],
      note: "The AI layer now emits a spatial heatmap, sequence forecast, confidence score, and material recommendation stream.",
    },
    {
      accent: "#55bde8",
      title: "Primary Structure",
      category: "Structure - Fuselage & Joints",
      status: structural?.limiting_location ?? "standby",
      specs: [
        ["Joint Stress", `${formatNumber(structural?.joint_stress_mpa, 0)} MPa`],
        ["Thermal Stress", `${formatNumber(structural?.thermal_stress_mpa, 0)} MPa`],
        ["Fatigue", `${formatNumber((structural?.fatigue_damage ?? 0) * 100, 2)}%`],
        ["Ablation", `${formatNumber(structural?.ablation_depth_mm, 3)} mm`],
        ["RUL", `${structural?.remaining_life_cycles ?? 120} cycles`],
      ],
      note: "Thermomechanical stress, panel-joint concentration, fatigue, ablation, and remaining useful life are tracked per mission.",
    },
    {
      accent: "#f0c04f",
      title: "Mission Replay Dataset",
      category: "ML Pipeline - Training Data",
      status: state ? "recording" : "ready",
      specs: [
        ["Simulation ID", state?.simulation_id ?? "--"],
        ["Samples", state ? "streaming JSONL" : "awaiting run"],
        ["Schema", "telemetry contract"],
        ["Use Case", "LSTM / RF / GP"],
        ["Reports", "markdown export"],
      ],
      note: "Every run can be replayed from generated JSONL telemetry, giving the project a credible path from synthetic simulation to trained models.",
    },
  ];
}

function ComponentCard({ card }: { card: ComponentCardData }) {
  return (
    <article className="system-card" style={{ "--accent": card.accent } as CSSProperties}>
      <div className="system-card-head">
        <div>
          <h2>{card.title}</h2>
          <span>{card.category}</span>
        </div>
        <b>{card.status}</b>
      </div>
      <div className="system-specs">
        {card.specs.map(([label, value]) => (
          <p key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </p>
        ))}
      </div>
      <p className="system-note">{card.note}</p>
    </article>
  );
}

export function SystemComponentsView({ mission, state }: SystemComponentsViewProps) {
  const cards = buildCards(mission, state);

  return (
    <section className="systems-page">
      <header className="systems-header">
        <p>Vehicle Subsystem Specifications - All Components - Current Simulation State</p>
        <strong>{state ? `Live: ${state.aircraft.flight_phase} / Mach ${state.aircraft.mach.toFixed(2)}` : "Start a mission for live values"}</strong>
      </header>

      <div className="systems-grid">
        {cards.map((card) => (
          <ComponentCard key={card.title} card={card} />
        ))}
      </div>
    </section>
  );
}
