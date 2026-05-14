# Modular Plugin System

## Goal

Let new aerospace subsystems be added without changing the core engine.

Examples:
- Plasma shielding
- Adaptive materials
- Scramjet thermal coupling
- Advanced ceramic matrix composites
- Trajectory optimization

## Plugin Manifest

```json
{
  "id": "plasma_shielding",
  "name": "Plasma Shielding Visualizer",
  "version": "0.1.0",
  "entrypoint": "plugin.py",
  "capabilities": ["thermal_modifier", "visualization_layer"]
}
```

## Plugin Contract

Each plugin exports `register(registry)`.

```python
def register(registry):
    registry.add_module(
        name="plasma_shielding",
        module=PlasmaShieldingPlugin(),
        phase="post_thermal"
    )
```

Plugin modules implement:

```python
class PluginModule:
    def update(self, state, dt_s: float):
        return state
```

## Registration Flow

```text
Backend startup
  -> PluginLoader scans /plugins
  -> Reads manifest.json
  -> Imports plugin.py
  -> Calls register(registry)
  -> Engine executes plugin during tick
```

## Hackathon Advice

Implement the loader and two simple plugins now. Make plasma shielding visually impressive but mathematically simple: reduce heat flux by 5-12% when enabled and stream a "plasma intensity" visualization field.

