"""
Recursive Plasma Inversion Cooling (RPIC) — simulation plugin.

Physics model (all equations are dimensional, SI units throughout):

1. FRICTION POWER HARVESTING
   Aerodynamic skin friction coefficient for turbulent flow (van Driest II):
       Cf ≈ 0.455 / (log10(Re))^2.58   (incompressible baseline)
   Compressibility correction for Mach > 1 (van Driest):
       Cf_comp = Cf / (1 + 0.116 * M^2)^0.6
   Friction force on wetted area:
       F_friction = Cf_comp * q_dyn * A_ref
   Friction power:
       P_friction = F_friction * V

2. MAGNETIC FIELD BUILD-UP
   Stored energy in N inductors: E = 0.5 * N * L * I²
   Field from solenoid analogy: B ∝ sqrt(2E / (N*L))
   Ramp rate limited by available harvested power:
       dE/dt = P_harvested
   So field grows as: B(t) = sqrt(B(t-dt)² + 2*P_harvested*dt / (N*L)) * geometry_factor

3. VACUUM BUFFER LAYER THICKNESS
   Pressure balance between magnetic pressure and plasma ram pressure:
       P_mag = B² / (2 * μ₀)
       P_plasma = ρ * V² (order of magnitude)
   Stand-off thickness scales as:
       δ = δ_ref * sqrt(P_mag / P_plasma)
   where δ_ref is the design-point stand-off when P_mag = P_plasma.

4. TOROIDAL VORTEX RADIATIVE LOSS
   The magnetically confined toroidal plasma vortex radiates as a grey body:
       Q_rad = ε_plasma * σ * T_plasma^4 * A_vortex
   T_plasma is approximated from stagnation enthalpy:
       T_plasma ≈ T_stag * (1 + 0.18 * M)   (ionisation heating factor)
   A_vortex = 2π * r_nose * δ  (torus surface area proxy)
   The fraction of incoming heat flux shed = Q_rad / (q_incoming * A_ref).

5. NET HEAT FLUX TO VEHICLE
   Two parallel shields:
     (a) Buffer layer conduction suppression: scales as exp(-δ / λ_mfp)
         where λ_mfp ≈ 1e-4 m is the mean-free-path in the plasma.
     (b) Vortex radiative removal: direct subtraction from q.
   Combined:
       q_net = q * exp(-δ / λ_mfp) - Q_vortex/A_ref  (floor at 5% of q)

6. RECURSIVE FEEDBACK GAIN
   d(cooling_fraction)/d(Mach) — positive means faster = better cooled.
   Computed as a finite difference against the previous tick's values.
"""

import math
from app.schemas.rpic import RPICConfig, RPICState

# Physical constants
MU_0   = 1.2566e-6   # H/m  permeability of free space
SIGMA  = 5.6704e-8   # W/m²/K⁴  Stefan-Boltzmann
LAMBDA_MFP = 1.0e-4  # m  plasma mean free path at hypersonic shock layer


def _van_driest_cf(mach: float, reynolds: float) -> float:
    """
    Turbulent skin friction coefficient with van Driest II compressibility
    correction.  Reynolds number estimated from velocity, altitude, and a
    reference length of 10 m (fuselage mid-body).
    """
    re = max(reynolds, 1e5)
    cf_incomp = 0.455 / (math.log10(re) ** 2.58)
    cf_comp   = cf_incomp / (1.0 + 0.116 * mach ** 2) ** 0.6
    return max(cf_comp, 1e-5)


def _estimate_reynolds(velocity_m_s: float, density: float, altitude_m: float) -> float:
    """
    Re = ρ V L / μ
    Dynamic viscosity from Sutherland's law (T from ISO atmosphere proxy).
    """
    T_approx = max(180.0, 288.15 - 0.0065 * min(altitude_m, 11_000))
    mu = 1.458e-6 * T_approx ** 1.5 / (T_approx + 110.4)   # Sutherland
    L  = 10.0   # reference length [m]
    return density * velocity_m_s * L / max(mu, 1e-8)


class RPICPlugin:
    name = "rpic"

    def __init__(self, config: RPICConfig | None = None) -> None:
        self.config = config or RPICConfig()
        self._prev_vortex_fraction: float = 0.0
        self._prev_mach: float = 0.0

    def update(self, state, dt_s: float):
        cfg  = self.config
        rpic: RPICState = state.rpic

        mach     = state.aircraft.mach
        altitude = state.aircraft.altitude_m
        velocity = state.aircraft.velocity_m_s
        rho      = state.aerodynamic.density_kg_m3
        q_dyn    = state.aerodynamic.dynamic_pressure_pa
        q_in     = state.thermal.heat_flux_w_m2    # from Fay-Riddell (pre-cooling)
        A_ref    = state.vehicle.reference_area_m2
        r_nose   = state.vehicle.nose_radius_m
        T_stag   = state.aerodynamic.stagnation_temperature_k

        # ---------------------------------------------------------------
        # GATE: only active above min Mach
        # ---------------------------------------------------------------
        if mach < cfg.min_mach_activate or not cfg.enabled:
            rpic.active  = False
            rpic.status  = "inactive"
            rpic.heat_flux_reduction_w_m2 = 0.0
            rpic.net_heat_flux_w_m2       = q_in
            state.rpic = rpic
            return state

        rpic.active = True

        # ---------------------------------------------------------------
        # 1. FRICTION POWER HARVESTING
        # ---------------------------------------------------------------
        re = _estimate_reynolds(velocity, rho, altitude)
        cf = _van_driest_cf(mach, re)
        F_friction       = cf * q_dyn * A_ref                  # [N]
        P_friction       = F_friction * velocity                # [W]
        P_harvested      = P_friction * cfg.harvester_efficiency

        rpic.friction_power_w  = round(P_friction, 1)
        rpic.harvested_power_w = round(P_harvested, 1)

        # ---------------------------------------------------------------
        # 2. MAGNETIC FIELD BUILD-UP  (inductor energy model)
        # ---------------------------------------------------------------
        N  = cfg.magnet_count
        L  = cfg.coil_inductance_h

        # Increment stored energy by harvested power this tick
        rpic.energy_stored_j = max(
            0.0,
            rpic.energy_stored_j + P_harvested * dt_s
        )
        # Cap at design-point saturation: E_max = 0.5 * N * L * I_max²
        # where I_max gives target field.  B_target ≈ µ₀ * N * I / length
        # For a fixed geometry, E_max proportional to B_target²:
        E_max = 0.5 * N * L * (cfg.target_field_tesla / (MU_0 * N)) ** 2
        rpic.energy_stored_j = min(rpic.energy_stored_j, E_max)

        # Field from stored energy: B = sqrt(2 * E / (N * L)) * geometry factor
        geometry_factor   = 0.72   # accounts for non-ideal coil packing
        B_raw             = math.sqrt(2.0 * rpic.energy_stored_j / max(N * L, 1e-9))
        B_field           = min(B_raw * geometry_factor, cfg.target_field_tesla)
        prev_field        = rpic.field_strength_t
        rpic.field_strength_t  = round(B_field, 4)
        rpic.field_ramp_rate_t_s = round((B_field - prev_field) / max(dt_s, 1e-9), 4)

        # ---------------------------------------------------------------
        # 3. VACUUM BUFFER LAYER THICKNESS
        # ---------------------------------------------------------------
        P_mag    = (B_field ** 2) / (2.0 * MU_0)           # magnetic pressure [Pa]
        P_plasma = rho * velocity ** 2                       # plasma ram pressure [Pa]
        ratio    = math.sqrt(max(P_mag / max(P_plasma, 1.0), 0.0))
        delta    = cfg.nose_stand_off_m * ratio              # buffer layer thickness [m]

        rpic.buffer_layer_m          = round(delta, 6)
        rpic.plasma_standoff_achieved = delta >= cfg.nose_stand_off_m * 0.8

        # ---------------------------------------------------------------
        # 4. TOROIDAL VORTEX RADIATIVE LOSS
        # ---------------------------------------------------------------
        eps_plasma  = 0.85                                   # grey body emissivity of plasma
        T_plasma    = T_stag * (1.0 + 0.18 * mach)          # ionisation-elevated temperature [K]
        A_vortex    = 2.0 * math.pi * r_nose * max(delta, 1e-5)  # torus surface area proxy [m²]

        Q_vortex_total  = eps_plasma * SIGMA * T_plasma ** 4 * A_vortex   # [W]
        Q_vortex_per_m2 = Q_vortex_total / max(A_ref, 1.0)                # [W/m²]
        vortex_fraction = min(0.60, Q_vortex_per_m2 / max(q_in, 1.0))

        rpic.vortex_radiative_loss_w_m2 = round(Q_vortex_per_m2, 1)
        rpic.vortex_cooling_fraction    = round(vortex_fraction, 4)

        # ---------------------------------------------------------------
        # 5. NET HEAT FLUX REDUCTION
        # ---------------------------------------------------------------
        # (a) Conductive suppression through buffer layer
        buffer_suppression = math.exp(-delta / LAMBDA_MFP)  # 0 = perfect shield, 1 = no shield

        # (b) Combined net flux (floor at 5% to prevent unphysical negatives)
        q_after_buffer  = q_in * buffer_suppression
        q_net           = max(q_in * 0.05, q_after_buffer - Q_vortex_per_m2)

        reduction       = q_in - q_net
        rpic.heat_flux_reduction_w_m2 = round(reduction, 1)
        rpic.net_heat_flux_w_m2       = round(q_net, 1)

        # COP: heat removed per watt of harvested power (dimensionless)
        rpic.cop = round(reduction * A_ref / max(P_harvested, 1.0), 2)

        # ---------------------------------------------------------------
        # 6. RECURSIVE FEEDBACK GAIN
        # ---------------------------------------------------------------
        d_mach    = mach - self._prev_mach
        d_cooling = vortex_fraction - self._prev_vortex_fraction
        rpic.feedback_gain = round(
            d_cooling / d_mach if abs(d_mach) > 1e-4 else 0.0, 4
        )
        self._prev_mach            = mach
        self._prev_vortex_fraction = vortex_fraction

        # ---------------------------------------------------------------
        # Status label
        # ---------------------------------------------------------------
        if B_field < cfg.target_field_tesla * 0.25:
            rpic.status = "ramping"
        elif B_field >= cfg.target_field_tesla * 0.95:
            rpic.status = "saturated"
        else:
            rpic.status = "active"

        # ---------------------------------------------------------------
        # WRITE BACK to thermal state
        # Replaces the stub in the old plasma_shielding plugin.
        # ---------------------------------------------------------------
        state.thermal.heat_flux_w_m2     = round(q_net, 1)
        state.thermal.net_heat_flux_w_m2 = round(q_net, 1)
        state.rpic = rpic
        return state


def register(registry):
    registry.add_module("rpic", RPICPlugin(), phase="post_thermal")