from dataclasses import dataclass
from typing import Protocol

from app.schemas.digital_twin import DigitalTwinState


class RuntimeModule(Protocol):
    name: str

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        ...


@dataclass
class RegisteredPlugin:
    name: str
    module: RuntimeModule
    phase: str = "post_thermal"


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[RegisteredPlugin] = []

    def add_module(self, name: str, module: RuntimeModule, phase: str = "post_thermal") -> None:
        self._plugins = [plugin for plugin in self._plugins if not (plugin.name == name and plugin.phase == phase)]
        self._plugins.append(RegisteredPlugin(name=name, module=module, phase=phase))

    def run_phase(self, phase: str, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        for plugin in self._plugins:
            if plugin.phase == phase:
                state = plugin.module.update(state, dt_s)
        return state

    def list_plugins(self) -> list[dict]:
        return [{"name": item.name, "phase": item.phase} for item in self._plugins]
