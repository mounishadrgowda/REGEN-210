from pydantic import BaseModel


class PlasmaShieldingState(BaseModel):
    enabled: bool = True
    magnetic_field_t: float = 1.2
    hall_parameter: float = 0
    reduction_factor: float = 0
    heat_flux_before_w_m2: float = 0
    heat_flux_after_w_m2: float = 0
    power_draw_kw: float = 0
