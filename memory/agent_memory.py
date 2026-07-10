from __future__ import annotations

import json
from pathlib import Path


class AgentMemory:
    """A JSON-backed memory store for session state and workspace restoration."""

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path or Path(__file__).resolve().parent / "session_memory.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, object] = {}
        self.load()

    def load(self) -> None:
        if self.storage_path.exists():
            with self.storage_path.open("r", encoding="utf-8") as handle:
                self._data = json.load(handle)
        else:
            self._data = {}

    def save(self) -> None:
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2)

    def set(self, key: str, value: object) -> None:
        self._data[key] = value
        self.save()

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self.save()

    def restore(self, key: str, default=None):
        return self.get(key, default)

