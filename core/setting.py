from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SettingsManager:
    """JSON-backed settings manager for the IDE."""

    def __init__(self, settings_path: str | Path | None = None):
        self.settings_path = Path(settings_path or Path(__file__).resolve().parent.parent / "config" / "settings.json")
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.settings_path.exists():
            self._data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        else:
            self._data = {
                "theme": "dark",
                "font_size": 12,
                "font_family": "Consolas",
                "auto_save": True,
                "auto_update": True,
            }

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def save(self) -> None:
        self.settings_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
