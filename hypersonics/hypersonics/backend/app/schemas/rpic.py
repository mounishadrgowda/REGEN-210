from pydantic import BaseModel


class RPICState(BaseModel):
    enabled: bool = True
    magnetic_field_t: float = 1.2
    plasma_density_m3: float = 0
    ionization_fraction: float = 0
    heat_flux_reduction: float = 0
    control_effort: float = 0
    power_draw_kw: float = 0
