from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict


class PluginSDK:
    """Minimal plugin SDK for registering IDE extensions and commands."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()
        self.plugins: Dict[str, Callable[..., object]] = {}

    def register(self, name: str, handler: Callable[..., object]) -> None:
        self.plugins[name] = handler

    def list_plugins(self) -> list[str]:
        return sorted(self.plugins)
