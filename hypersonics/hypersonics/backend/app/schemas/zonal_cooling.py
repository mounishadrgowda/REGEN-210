"""
Zonal regenerative cooling schema.

The vehicle surface is divided into thermal zones. Each zone has its
own heat flux, wall temperature, and an independently commanded LH₂
flow fraction. The AI allocator decides how to split total coolant
mass flow across zones every tick.
"""

from pydantic import BaseModel, Field
from typing import Literal

ZoneID = Literal[
    "nose_cap",
    "leading_edge_port",
    "leading_edge_starboard",
    "windward_panel",
    "leeward_panel",
    "base_heat_shield",
]

ALL_ZONES: list[ZoneID] = [
    "nose_cap",
    "leading_edge_port",
    "leading_edge_starboard",
    "windward_panel",
    "leeward_panel",
    "base_heat_shield",
]

# Fraction of total vehicle reference area each zone occupies.
# Must sum to 1.0.
ZONE_AREA_FRACTIONS: dict[str, float] = {
    "nose_cap":               0.04,
    "leading_edge_port":      0.09,
    "leading_edge_starboard": 0.09,
    "windward_panel":         0.38,
    "leeward_panel":          0.28,
    "base_heat_shield":       0.12,
}

# Geometric heat-flux multipliers relative to stagnation point.
# Nose = 1.0 (reference), leading edges slightly lower, leeward panel much lower.
ZONE_FLUX_MULTIPLIERS: dict[str, float] = {
    "nose_cap":               1.00,
    "leading_edge_port":      0.82,
    "leading_edge_starboard": 0.82,
    "windward_panel":         0.61,
    "leeward_panel":          0.18,
    "base_heat_shield":       0.35,
}

# Minimum flow fraction each zone must always receive (safety floor).
ZONE_MIN_FLOW: dict[str, float] = {
    "nose_cap":               0.08,
    "leading_edge_port":      0.06,
    "leading_edge_starboard": 0.06,
    "windward_panel":         0.05,
    "leeward_panel":          0.02,
    "base_heat_shield":       0.03,
}


class ZoneThermalState(BaseModel):
    zone_id: ZoneID
    area_m2: float = 0.0
    heat_flux_w_m2: float = 0.0          # incoming heat flux for this zone
    wall_temp_k: float = 300.0           # current wall temperature
    flow_fraction: float = 0.0           # fraction of total LH₂ mass flow assigned here
    mass_flow_kg_s: float = 0.0          # absolute LH₂ flow [kg/s]
    heat_removed_w_m2: float = 0.0       # heat extracted [W/m²]
    cooling_efficiency: float = 0.0      # local efficiency [0–1]
    net_heat_flux_w_m2: float = 0.0      # after cooling
    thermal_margin: float = 1.0          # (T_max - T_wall) / T_max
    lh2_consumed_kg: float = 0.0         # cumulative LH₂ used (= fuel burned)
    priority: float = 0.0                # AI-assigned priority score [0–1]


class ZonalCoolingState(BaseModel):
    """Aggregated zonal cooling state, broadcast on every WebSocket tick."""
    active: bool = True
    zones: list[ZoneThermalState] = Field(default_factory=list)

    # Totals
    total_lh2_flow_kg_s: float = 0.0
    total_heat_removed_w: float = 0.0
    total_lh2_consumed_kg: float = 0.0  # mission-cumulative fuel cost

    # AI allocator diagnostics
    allocator_iterations: int = 0
    allocation_converged: bool = False
    peak_zone: str = ""                  # zone ID with highest wall temperature
    coldest_zone: str = ""               # zone with most thermal headroom
    fuel_saved_vs_uniform_kg_s: float = 0.0   # efficiency gain over dumb uniform split