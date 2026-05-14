# TPS Engine Design

## Purpose

The TPS engine produces credible, explainable demo calculations without claiming CFD-grade accuracy.

## Simplified Formulas

Velocity:

```text
v = Mach * speed_of_sound
```

Atmospheric density proxy:

```text
rho = 1.225 * exp(-altitude_m / 8500)
```

Convective heat flux proxy:

```text
q = C * sqrt(rho / nose_radius_m) * v^3
```

Use `C = 1.83e-4 * 0.000001` as a scaled demo constant so values stay dashboard-friendly.

Cooling heat removal:

```text
q_removed = mass_flow * coolant_cp * delta_t / surface_area
cooling_efficiency = clamp(q_removed / q, 0, 0.85)
```

Wall temperature proxy:

```text
T_wall = ambient_temp + (q_net * thickness_factor / material_conductivity) * scale
```

Thermal margin:

```text
margin = (material_max_temp - T_wall) / material_max_temp
```

Failure warning:

```text
failure = margin < 0.08 or T_wall > material_max_temp
```

## Module Responsibilities

Aerodynamics:
- Estimate density, velocity, dynamic pressure, shock cone angle.

Thermal:
- Estimate heat flux, thermal load, wall temperature.

Cooling:
- Estimate heat removed and cooling efficiency.

Material Risk:
- Compare material limits against thermal state.
- Generate alerts.

Sustainability:
- Score material and cooling choices.

