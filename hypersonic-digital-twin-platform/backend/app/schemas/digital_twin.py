from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["nominal", "guarded", "critical"]


class VehicleConfig(BaseModel):
    name: str = "AETHER-HX1"
    nose_radius_m: float = 0.35
    reference_area_m2: float = 22.0


class InitialConditions(BaseModel):
    mach: float = 6.8
    altitude_m: float = 31000
    angle_of_attack_deg: float = 4.0
    duration_s: int = 180


class TPSConfig(BaseModel):
    material_id: str = "c_phenolic"
    thickness_mm: float = 42
    surface_area_m2: float = 48.5


class CoolingConfig(BaseModel):
    enabled: bool = True
    coolant: str = "liquid_hydrogen"
    mass_flow_kg_s: float = 0.8


class SimulationStartRequest(BaseModel):
    mission_id: str = "demo-mission-001"
    vehicle: VehicleConfig = Field(default_factory=VehicleConfig)
    initial_conditions: InitialConditions = Field(default_factory=InitialConditions)
    tps: TPSConfig = Field(default_factory=TPSConfig)
    cooling: CoolingConfig = Field(default_factory=CoolingConfig)


class AircraftState(BaseModel):
    mach: float
    altitude_m: float
    angle_of_attack_deg: float
    velocity_m_s: float = 0


class AerodynamicState(BaseModel):
    density_kg_m3: float = 0
    dynamic_pressure_pa: float = 0
    shock_cone_angle_deg: float = 0
    stagnation_temperature_k: float = 0


class ThermalState(BaseModel):
    heat_flux_w_m2: float = 0
    net_heat_flux_w_m2: float = 0
    thermal_load_mj_m2: float = 0
    max_surface_temp_k: float = 300
    thermal_margin: float = 1


class CoolingState(BaseModel):
    enabled: bool = True
    coolant: str = "liquid_hydrogen"
    mass_flow_kg_s: float = 0.8
    heat_removed_w_m2: float = 0
    efficiency: float = 0


class RiskState(BaseModel):
    level: RiskLevel = "nominal"
    score: float = 0
    failure_warning: bool = False
    recommended_action: str = "Maintain current TPS profile"


class SustainabilityState(BaseModel):
    score: float = 0.72
    material_reuse_potential: float = 0.5
    coolant_penalty: float = 0.1


class AIPredictionState(BaseModel):
    model_stage: str = "demo-surrogate"
    material_recommendation: list[str] = Field(default_factory=list)
    failure_probability: float = 0
    anomaly_score: float = 0
    heat_forecast_k: list[float] = Field(default_factory=list)


class Alert(BaseModel):
    severity: RiskLevel
    code: str
    message: str


class DigitalTwinState(BaseModel):
    simulation_id: str
    mission_id: str
    time_s: float = 0
    vehicle: VehicleConfig
    tps: TPSConfig
    aircraft: AircraftState
    aerodynamic: AerodynamicState = Field(default_factory=AerodynamicState)
    thermal: ThermalState = Field(default_factory=ThermalState)
    cooling: CoolingState = Field(default_factory=CoolingState)
    risk: RiskState = Field(default_factory=RiskState)
    sustainability: SustainabilityState = Field(default_factory=SustainabilityState)
    ai: AIPredictionState = Field(default_factory=AIPredictionState)
    alerts: list[Alert] = Field(default_factory=list)


class TPSEvaluateRequest(BaseModel):
    mach: float = 7.2
    altitude_m: float = 28000
    nose_radius_m: float = 0.35
    material_id: str = "c_phenolic"
    thickness_mm: float = 42
    coolant_mass_flow_kg_s: float = 0.8

