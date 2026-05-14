import importlib.util
import json
from pathlib import Path

from app.plugins.registry import PluginRegistry


def load_plugins(registry: PluginRegistry) -> None:
    project_root = Path(__file__).resolve().parents[3]
    plugin_root = project_root / "plugins"
    if not plugin_root.exists():
        return

    for manifest_path in plugin_root.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entrypoint = manifest_path.parent / manifest.get("entrypoint", "plugin.py")
        if not entrypoint.exists():
            continue

        spec = importlib.util.spec_from_file_location(f"aether_plugin_{manifest['id']}", entrypoint)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "register"):
            module.register(registry)

