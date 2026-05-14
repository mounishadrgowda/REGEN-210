import type { SimulationStartRequest } from "./types";

export const defaultMission: SimulationStartRequest = {
  mission_id: "demo-mission-001",
  vehicle: {
    name: "AETHER-HX1",
    nose_radius_m: 0.35,
    reference_area_m2: 22,
  },
  initial_conditions: {
    mach: 6.8,
    altitude_m: 31000,
    angle_of_attack_deg: 4,
    duration_s: 180,
  },
  tps: {
    material_id: "c_phenolic",
    thickness_mm: 42,
    surface_area_m2: 48.5,
  },
  cooling: {
    enabled: true,
    coolant: "liquid_hydrogen",
    mass_flow_kg_s: 0.8,
  },
};

