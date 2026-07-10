from __future__ import annotations

from typing import Callable


class CommandRegistry:
    """Simple registry for IDE commands and actions."""

    def __init__(self):
        self._commands: dict[str, Callable[[], None]] = {}

    def register(self, name: str, callback: Callable[[], None]) -> None:
        self._commands[name] = callback

    def run(self, name: str) -> None:
        callback = self._commands.get(name)
        if callback is None:
            raise KeyError(name)
        callback()

    def list_commands(self) -> list[str]:
        return sorted(self._commands)
