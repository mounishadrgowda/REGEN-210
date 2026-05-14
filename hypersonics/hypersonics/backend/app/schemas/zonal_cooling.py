from pydantic import BaseModel, Field


class CoolingZoneState(BaseModel):
    name: str
    heat_flux_w_m2: float = 0
    coolant_fraction: float = 0
    efficiency: float = 0
    surface_temp_k: float = 300
    thermal_margin: float = 1
    status: str = "nominal"


class ZonalCoolingState(BaseModel):
    enabled: bool = True
    active_zone: str = "nose"
    balance_quality: float = 1
    max_zone_temp_k: float = 300
    min_zone_margin: float = 1
    zones: list[CoolingZoneState] = Field(default_factory=list)
