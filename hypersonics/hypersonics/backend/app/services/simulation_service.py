import asyncio
from pathlib import Path

from app.core.config import settings
from app.realtime.manager import telemetry_manager
from app.schemas.digital_twin import DigitalTwinState, SimulationStartRequest
from app.simulation.engine import SimulationEngine


class SimulationService:
    def __init__(self) -> None:
        self.engine = SimulationEngine()
        self.states: dict[str, DigitalTwinState] = {}
        self.missions: dict[str, SimulationStartRequest] = {}
        self.histories: dict[str, list[DigitalTwinState]] = {}
        self.running: set[str] = set()
        self.max_history_samples = 600
        self.dataset_dir = Path(__file__).resolve().parents[3] / "datasets" / "generated"

    async def start(self, request: SimulationStartRequest) -> DigitalTwinState:
        state = self.engine.create_state(request)
        self.states[state.simulation_id] = state
        self.missions[state.simulation_id] = request.model_copy(deep=True)
        self.histories[state.simulation_id] = [state.model_copy(deep=True)]
        self.running.add(state.simulation_id)
        asyncio.create_task(self._run_loop(state.simulation_id))
        return state

    def latest(self, simulation_id: str | None = None) -> DigitalTwinState | None:
        if simulation_id:
            return self.states.get(simulation_id)
        if not self.states:
            return None
        return next(reversed(self.states.values()))

    def mission(self, simulation_id: str | None) -> SimulationStartRequest | None:
        if not simulation_id:
            return None
        return self.missions.get(simulation_id)

    def history(self, simulation_id: str | None) -> list[DigitalTwinState]:
        if not simulation_id:
            return []
        return self.histories.get(simulation_id, [])

    def tick_once(self, simulation_id: str, dt_s: float = 0.2) -> DigitalTwinState:
        state = self.states[simulation_id]
        state = self.engine.tick(state, dt_s)
        self.states[simulation_id] = state
        samples = self.histories.setdefault(simulation_id, [])
        samples.append(state.model_copy(deep=True))
        if len(samples) > self.max_history_samples:
            del samples[: len(samples) - self.max_history_samples]
        self._record_sample(state)
        return state

    def stop(self, simulation_id: str) -> bool:
        self.running.discard(simulation_id)
        return simulation_id in self.states

    async def _run_loop(self, simulation_id: str) -> None:
        dt_s = 1.0 / settings.simulation_tick_hz
        while simulation_id in self.running:
            state = self.tick_once(simulation_id, dt_s)
            await telemetry_manager.broadcast(
                {
                    "type": "telemetry.tick",
                    "simulation_id": simulation_id,
                    "time_s": round(state.time_s, 2),
                    "state": state.model_dump(),
                }
            )
            await asyncio.sleep(dt_s)

    def _record_sample(self, state: DigitalTwinState) -> None:
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        sample_path = self.dataset_dir / f"{state.simulation_id}.jsonl"
        with sample_path.open("a", encoding="utf-8") as file:
            file.write(state.model_dump_json() + "\n")


simulation_service = SimulationService()
