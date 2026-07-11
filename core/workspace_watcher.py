from __future__ import annotations

from pathlib import Path
from typing import List


class WorkspaceWatcher:
    """A lightweight watcher that tracks file changes for background indexing refreshes."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()
        self._state: dict[str, str] = {}

    def scan(self) -> List[str]:
        changed: List[str] = []
        for path in self.workspace.rglob("*"):
            if path.is_file():
                relative = path.relative_to(self.workspace).as_posix()
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                previous = self._state.get(relative)
                if previous != content:
                    changed.append(relative)
                    self._state[relative] = content
        return changed
