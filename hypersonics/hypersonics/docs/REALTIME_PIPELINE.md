# Realtime System Design

## WebSocket Architecture

```text
Simulation Tick Loop
  -> Digital Twin Snapshot
  -> TelemetryManager.broadcast()
  -> WebSocket clients
  -> Frontend state store
  -> Charts, heatmap, 3D overlays, alerts
```

## Tick System

Recommended hackathon settings:
- Tick rate: 5 Hz backend simulation.
- Frontend chart update: throttle to 10 FPS maximum.
- 3D animation: render at browser frame rate using latest snapshot.

## Message Types

```json
{ "type": "telemetry.tick", "state": {} }
{ "type": "alert.raised", "alert": {} }
{ "type": "simulation.completed", "summary": {} }
```

## Frontend Update Pipeline

1. WebSocket receives snapshot.
2. `digitalTwinStore` merges it.
3. Charts append telemetry points.
4. Vehicle visualization updates material colors.
5. Thermal overlay interpolates heatmap grid.
6. Alert rail displays warnings.

## Scale Path

For a cloud version:
- WebSocket service becomes independent.
- Redis Pub/Sub distributes telemetry.
- Kafka/NATS stores high-throughput simulation streams.
- TimescaleDB persists historical mission telemetry.

