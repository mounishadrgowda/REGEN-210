# Digital Twin Architecture

## Twin State

The digital twin is a single structured state object updated every simulation tick.

```text
DigitalTwinState
  aircraft_state
  aerodynamic_state
  thermal_state
  cooling_state
  material_state
  structural_state
  sustainability_state
  ai_prediction_state
  alerts
```

## State Slices

Aircraft state:
- Mach number
- Altitude
- Angle of attack
- Velocity
- Vehicle geometry

Aerodynamic state:
- Dynamic pressure
- Shock cone angle
- Stagnation temperature estimate
- Heating coefficient

Thermal state:
- Heat flux
- Wall temperature
- Thermal load
- Peak surface zone
- Ablation estimate

Cooling state:
- Coolant type
- Mass flow
- Heat removed
- Efficiency
- Pump load estimate

AI prediction state:
- Heat forecast
- Material recommendation
- Failure probability
- Anomaly score
- Optimization hint

## Module Communication

Modules do not call each other directly. They read and update the shared twin state through the engine.

```text
Engine Tick
  -> AerodynamicsModule.update(state)
  -> ThermalModule.update(state)
  -> CoolingModule.update(state)
  -> MaterialRiskModule.update(state)
  -> SustainabilityModule.update(state)
  -> MLInferenceAdapter.update(state)
  -> PluginRegistry.run_all(state)
  -> TelemetryPublisher.broadcast(state)
```

This keeps the design modular. A future high-fidelity CFD adapter can replace the aerodynamic module without changing the frontend.

