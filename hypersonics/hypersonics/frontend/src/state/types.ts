export type RiskLevel = "nominal" | "guarded" | "critical";

export interface SimulationStartRequest {
  mission_id: string;
  vehicle: {
    name: string;
    nose_radius_m: number;
    reference_area_m2: number;
    drag_coefficient: number;
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
  plasma_control: {
    enabled: boolean;
    magnetic_field_t: number;
  };
}

export interface DigitalTwinState {
  simulation_id: string;
  mission_id: string;
  time_s: number;
  vehicle: SimulationStartRequest["vehicle"];
  tps: SimulationStartRequest["tps"];
  aircraft: {
    mach: number;
    altitude_m: number;
    angle_of_attack_deg: number;
    velocity_m_s: number;
    target_mach: number;
    mach_rate_per_s: number;
    cruise_altitude_m: number;
    mission_duration_s: number;
    flight_phase: string;
  };
  aerodynamic: {
    density_kg_m3: number;
    dynamic_pressure_pa: number;
    shock_cone_angle_deg: number;
    stagnation_temperature_k: number;
  };
  thermal: {
    heat_flux_w_m2: number;
    net_heat_flux_w_m2: number;
    thermal_load_mj_m2: number;
    max_surface_temp_k: number;
    thermal_margin: number;
  };
  cooling: { efficiency: number; heat_removed_w_m2: number; mass_flow_kg_s: number; coolant: string };
  zonal_cooling: {
    enabled: boolean;
    active_zone: string;
    balance_quality: number;
    max_zone_temp_k: number;
    min_zone_margin: number;
    zones: Array<{
      name: string;
      heat_flux_w_m2: number;
      coolant_fraction: number;
      efficiency: number;
      surface_temp_k: number;
      thermal_margin: number;
      status: string;
    }>;
  };
  plasma_shielding: {
    enabled: boolean;
    magnetic_field_t: number;
    hall_parameter: number;
    reduction_factor: number;
    heat_flux_before_w_m2: number;
    heat_flux_after_w_m2: number;
    power_draw_kw: number;
  };
  structural: {
    thermal_stress_mpa: number;
    joint_stress_mpa: number;
    fatigue_damage: number;
    ablation_depth_mm: number;
    cycles: number;
    remaining_life_cycles: number;
    failure_probability: number;
    limiting_location: string;
  };
  risk: { level: RiskLevel; score: number; recommended_action: string; failure_warning: boolean };
  sustainability: { score: number };
  rpic: {
    enabled: boolean;
    magnetic_field_t: number;
    plasma_density_m3: number;
    ionization_fraction: number;
    heat_flux_reduction: number;
    control_effort: number;
    power_draw_kw: number;
  };
  ai: {
    model_stage: string;
    material_recommendation: string[];
    failure_probability: number;
    anomaly_score: number;
    heat_forecast_k: number[];
    spatial_heatmap_k: number[][];
    maintenance_remaining_cycles: number;
    model_confidence: number;
    surrogate_notes: string[];
  };
  alerts: Array<{ severity: RiskLevel; code: string; message: string }>;
}

export interface TelemetryMessage {
  type: string;
  simulation_id: string;
  time_s: number;
  state: DigitalTwinState;
}

export interface MissionReport {
  status: "generated";
  report_id: string;
  generated_at: string;
  download_filename: string;
  report_path: string;
  executive_summary: {
    mission_generated: boolean;
    risk_level: RiskLevel;
    assessment: string;
    recommended_action: string;
  };
  scorecard: {
    overall: number;
    thermal_control: number;
    physics_depth: number;
    ml_readiness: number;
    reliability: number;
  };
  judge_highlights: string[];
  mission: {
    mission_id: string;
    simulation_id: string;
    vehicle_name: string;
    initial_mach: number;
    final_mach: number;
    target_mach: number;
    flight_phase: string;
    initial_altitude_m: number;
    final_altitude_m: number;
    cruise_altitude_m: number;
    final_velocity_m_s: number;
    angle_of_attack_deg: number;
    planned_duration_s: number;
    covered_duration_s: number;
    progress_pct: number;
    samples: number;
  };
  thermal: {
    material_id: string;
    thickness_mm: number;
    peak_heat_flux_w_m2: number;
    peak_heat_flux_mw_m2: number;
    avg_heat_flux_mw_m2: number;
    peak_net_heat_flux_w_m2: number;
    peak_net_heat_flux_mw_m2: number;
    peak_surface_temp_k: number;
    avg_surface_temp_k: number;
    final_surface_temp_k: number;
    minimum_thermal_margin: number;
    minimum_thermal_margin_pct: number;
    thermal_load_mj_m2: number;
  };
  cooling: {
    enabled: boolean;
    coolant: string;
    mass_flow_kg_s: number;
    average_efficiency_pct: number;
    final_heat_removed_w_m2: number;
    final_heat_removed_kw_m2: number;
    peak_heat_removed_kw_m2: number;
  };
  structural: {
    peak_thermal_stress_mpa: number;
    peak_joint_stress_mpa: number;
    final_thermal_stress_mpa: number;
    final_joint_stress_mpa: number;
    fatigue_damage_pct: number;
    ablation_depth_mm: number;
    cycles: number;
    remaining_life_cycles: number;
    failure_probability_pct: number;
    limiting_location: string;
  };
  risk: {
    level: RiskLevel;
    maximum_score: number;
    failure_warning: boolean;
    failure_probability_pct: number;
    anomaly_score: number;
    sustainability_score_pct: number;
  };
  intelligence: {
    model_stage: string;
    model_confidence_pct: number;
    material_recommendation: string[];
    heat_forecast_k: number[];
    heatmap: { min_k: number; max_k: number; avg_k: number; hotspot: string; rows: number; cols: number };
    maintenance_remaining_cycles: number;
    surrogate_notes: string[];
  };
  alerts: Array<{ severity: RiskLevel; code: string; message: string }>;
  recommendations: string[];
  markdown: string;
}

export interface DesignComponent {
  id: string;
  name: string;
  role: string;
  x: number;
  y: number;
  color: string;
  temp_k: number;
  status: string;
}

export interface DesignGeneratorResponse {
  model_stage: string;
  design_id: string;
  name: string;
  score: number;
  predicted: {
    baseline_heat_flux_w_m2: number;
    optimized_heat_flux_w_m2: number;
    heat_reduction_pct: number;
    surface_temp_k: number;
    thermal_margin: number;
    lift_to_drag: number;
    drag_coefficient: number;
    cooling_power_kw: number;
  };
  geometry: {
    nose_radius_m: number;
    leading_edge_radius_mm: number;
    wing_sweep_deg: number;
    compression_ramp_deg: number;
    reference_area_m2: number;
    wetted_area_m2: number;
  };
  materials: {
    nose: string;
    leading_edges: string;
    skin: string;
    coolant: string;
  };
  components: DesignComponent[];
  recommendations: string[];
  mission_patch: {
    vehicle: SimulationStartRequest["vehicle"];
    tps: SimulationStartRequest["tps"];
    cooling: SimulationStartRequest["cooling"];
  };
}
