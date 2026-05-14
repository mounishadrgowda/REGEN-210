export type RiskLevel = "nominal" | "guarded" | "critical";

export interface SimulationStartRequest {
  mission_id: string;
  vehicle: {
    name: string;
    nose_radius_m: number;
    reference_area_m2: number;
  };
  initial_conditions: {
    mach: number;
    altitude_m: number;
    angle_of_attack_deg: number;
    duration_s: number;
  };
  tps: {
    material_id: string;
    thickness_mm: number;
    surface_area_m2: number;
  };
  cooling: {
    enabled: boolean;
    coolant: string;
    mass_flow_kg_s: number;
  };
}

export interface DigitalTwinState {
  simulation_id: string;
  mission_id: string;
  time_s: number;
  aircraft: { mach: number; altitude_m: number; angle_of_attack_deg: number; velocity_m_s: number };
  aerodynamic: { shock_cone_angle_deg: number; dynamic_pressure_pa: number };
  thermal: {
    heat_flux_w_m2: number;
    net_heat_flux_w_m2: number;
    thermal_load_mj_m2: number;
    max_surface_temp_k: number;
    thermal_margin: number;
  };
  cooling: { efficiency: number; heat_removed_w_m2: number; mass_flow_kg_s: number; coolant: string };
  risk: { level: RiskLevel; score: number; recommended_action: string; failure_warning: boolean };
  sustainability: { score: number };
  ai: {
    model_stage: string;
    material_recommendation: string[];
    failure_probability: number;
    anomaly_score: number;
    heat_forecast_k: number[];
  };
  alerts: Array<{ severity: RiskLevel; code: string; message: string }>;
}

export interface TelemetryMessage {
  type: string;
  simulation_id: string;
  time_s: number;
  state: DigitalTwinState;
}

