"""
Recursive Plasma Inversion Cooling (RPIC) — state schema.

Tracks every quantity the physics model computes per tick:
  - energy harvested from aerodynamic friction
  - superconducting magnet field strength
  - vacuum buffer layer thickness
  - plasma toroidal vortex radiative loss
  - net heat flux reduction applied to the vehicle surface
"""

from pydantic import BaseModel, Field


class RPICConfig(BaseModel):
    """
    Operator-tunable parameters supplied at simulation start.
    These can be added to SimulationStartRequest if you want the
    frontend to expose them; defaults reflect a plausible near-future system.
    """
    enabled: bool = True

    # Magnet geometry
    magnet_count: int = 24                   # number of embedded coil segments
    coil_inductance_h: float = 0.018         # Henry per coil — drives field ramp speed
    target_field_tesla: float = 4.0          # design-point field strength at nose

    # Energy harvesting
    harvester_efficiency: float = 0.08       # fraction of friction power recovered (~8%)
    min_mach_activate: float = 5.5           # RPIC switches on above this Mach number

    # Plasma vortex geometry
    nose_stand_off_m: float = 0.12           # desired vacuum buffer thickness at nose [m]


class RPICState(BaseModel):
    """Live per-tick computed values broadcast over WebSocket."""

    active: bool = False

    # Energy loop
    friction_power_w: float = 0.0            # total aerodynamic friction power [W]
    harvested_power_w: float = 0.0           # power delivered to magnets [W]
    energy_stored_j: float = 0.0            # energy in magnet inductors [J]

    # Magnetic field
    field_strength_t: float = 0.0           # effective field at nose stagnation [T]
    field_ramp_rate_t_s: float = 0.0        # dB/dt this tick [T/s]

    # Plasma sheath interaction
    buffer_layer_m: float = 0.0             # vacuum gap between surface and plasma [m]
    plasma_standoff_achieved: bool = False   # True when buffer ≥ target stand-off

    # Toroidal vortex radiative cooling
    vortex_radiative_loss_w_m2: float = 0.0  # power radiated away by the vortex [W/m²]
    vortex_cooling_fraction: float = 0.0     # fraction of incoming q shed by vortex

    # Net effect on vehicle
    heat_flux_reduction_w_m2: float = 0.0   # total heat flux removed from surface [W/m²]
    net_heat_flux_w_m2: float = 0.0         # q after RPIC (written back to thermal state)
    cop: float = 0.0                         # coefficient of performance (Q_removed / P_input)

    # Feedback loop health
    feedback_gain: float = 0.0              # dCooling/dMach — the "recursive" metric
    status: str = "inactive"                # "inactive" | "ramping" | "active" | "saturated"