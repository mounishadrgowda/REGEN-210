import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { DigitalTwinState } from "../state/types";
import { IntelligenceRail } from "./IntelligenceRail";

const baseState: DigitalTwinState = {
  simulation_id: "sim_test",
  mission_id: "mission_test",
  time_s: 12,
  aircraft: { mach: 7.1, altitude_m: 30000, angle_of_attack_deg: 4, velocity_m_s: 2094 },
  aerodynamic: { shock_cone_angle_deg: 8.1, dynamic_pressure_pa: 34000 },
  thermal: {
    heat_flux_w_m2: 1800000,
    net_heat_flux_w_m2: 1050000,
    thermal_load_mj_m2: 18,
    max_surface_temp_k: 1420,
    thermal_margin: 0.32,
  },
  cooling: { efficiency: 0.42, heat_removed_w_m2: 720000, mass_flow_kg_s: 0.8, coolant: "liquid_hydrogen" },
  risk: { level: "guarded", score: 0.46, recommended_action: "Raise cooling flow", failure_warning: false },
  sustainability: { score: 0.76 },
  ai: {
    model_stage: "demo-surrogate",
    material_recommendation: ["reinforced_carbon_carbon", "c_phenolic"],
    failure_probability: 0.31,
    anomaly_score: 0.2,
    heat_forecast_k: [1430, 1450],
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
