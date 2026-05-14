import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { defaultMission } from "../state/defaultMission";
import type { DigitalTwinState } from "../state/types";
import { IntelligenceRail } from "./IntelligenceRail";

const baseState: DigitalTwinState = {
  simulation_id: "sim_test",
  mission_id: "mission_test",
  time_s: 12,
  vehicle: defaultMission.vehicle,
  tps: defaultMission.tps,
  aircraft: {
    mach: 7.1,
    altitude_m: 30000,
    angle_of_attack_deg: 4,
    velocity_m_s: 2094,
    target_mach: 7.8,
    mach_rate_per_s: 0.035,
    cruise_altitude_m: 35000,
    mission_duration_s: 180,
    flight_phase: "thermal-cruise",
  },
  aerodynamic: { density_kg_m3: 0.036, shock_cone_angle_deg: 8.1, dynamic_pressure_pa: 34000, stagnation_temperature_k: 2438 },
  thermal: {
    heat_flux_w_m2: 1800000,
    net_heat_flux_w_m2: 1050000,
    thermal_load_mj_m2: 18,
    max_surface_temp_k: 1420,
    thermal_margin: 0.32,
  },
  cooling: { efficiency: 0.42, heat_removed_w_m2: 720000, mass_flow_kg_s: 0.8, coolant: "liquid_hydrogen" },
  zonal_cooling: {
    enabled: true,
    active_zone: "nose",
    balance_quality: 0.91,
    max_zone_temp_k: 1420,
    min_zone_margin: 0.32,
    zones: [],
  },
  plasma_shielding: {
    enabled: true,
    magnetic_field_t: 1.2,
    hall_parameter: 0.5,
    reduction_factor: 0.06,
    heat_flux_before_w_m2: 1800000,
    heat_flux_after_w_m2: 1692000,
    power_draw_kw: 180,
  },
  structural: {
    thermal_stress_mpa: 210,
    joint_stress_mpa: 145,
    fatigue_damage: 0.04,
    ablation_depth_mm: 0.2,
    cycles: 2,
    remaining_life_cycles: 114,
    failure_probability: 0.18,
    limiting_location: "nose",
  },
  risk: { level: "guarded", score: 0.46, recommended_action: "Raise cooling flow", failure_warning: false },
  sustainability: { score: 0.76 },
  rpic: {
    enabled: true,
    magnetic_field_t: 1.2,
    plasma_density_m3: 4.2e17,
    ionization_fraction: 0.12,
    heat_flux_reduction: 0.08,
    control_effort: 0.44,
    power_draw_kw: 240,
  },
  ai: {
    model_stage: "demo-surrogate",
    material_recommendation: ["reinforced_carbon_carbon", "c_phenolic"],
    failure_probability: 0.31,
    anomaly_score: 0.2,
    heat_forecast_k: [1430, 1450],
    spatial_heatmap_k: [],
    maintenance_remaining_cycles: 114,
    model_confidence: 0.82,
    surrogate_notes: [],
  },
  alerts: [],
};

describe("IntelligenceRail", () => {
  it("renders AI model state and recommendation", () => {
    render(<IntelligenceRail state={baseState} />);

    expect(screen.getByText("demo-surrogate")).toBeInTheDocument();
    expect(screen.getByText("31%")).toBeInTheDocument();
    expect(screen.getByText("reinforced carbon carbon")).toBeInTheDocument();
    expect(screen.getByText("Raise cooling flow")).toBeInTheDocument();
  });
});
