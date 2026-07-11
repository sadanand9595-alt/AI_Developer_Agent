from __future__ import annotations

import importlib
from pathlib import Path
from typing import Callable, Dict


class PluginSystem:
    """A lightweight plugin registry with auto-discovery support."""

    def __init__(self, plugin_dir: str | Path | None = None):
        self.plugin_dir = Path(plugin_dir or Path(__file__).resolve().parent.parent / "plugins")
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self._plugins: Dict[str, Callable[..., object]] = {}

    def register(self, name: str, plugin: Callable[..., object]) -> None:
        self._plugins[name] = plugin

    def auto_discover(self) -> list[str]:
        discovered: list[str] = []
        for plugin_file in sorted(self.plugin_dir.glob("*.py")):
            if plugin_file.name.startswith("_"):
                continue
            module_name = plugin_file.stem
            try:
                module = importlib.import_module(f"plugins.{module_name}")
            except Exception:
                continue
            if hasattr(module, "PLUGIN"):
                self.register(module_name, getattr(module, "PLUGIN"))
                discovered.append(module_name)
        return discovered

    def get(self, name: str) -> Callable[..., object]:
        return self._plugins[name]

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins)
