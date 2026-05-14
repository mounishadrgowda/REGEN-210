from pydantic import BaseModel


class StructuralState(BaseModel):
    thermal_stress_mpa: float = 0
    joint_stress_mpa: float = 0
    fatigue_damage: float = 0
    ablation_depth_mm: float = 0
    cycles: int = 0
    remaining_life_cycles: int = 120
    failure_probability: float = 0
    limiting_location: str = "nose"
