from __future__ import annotations

from pathlib import Path

from core.file_scanner import FileScanner


class WorkspaceManager:
    """Small convenience wrapper around the existing workspace scanning utilities."""

    def __init__(self, workspace_path: str | Path):
        self.workspace = Path(workspace_path).expanduser().resolve()
        if not self.workspace.exists():
            raise FileNotFoundError(self.workspace)
        if not self.workspace.is_dir():
            raise NotADirectoryError(self.workspace)

        self.scanner = FileScanner(self.workspace)

    def discover_files(self) -> list[str]:
        return [info.relative_path for info in self.scanner.scan()]

    def read_file(self, file_path: str | Path) -> str:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace / path
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read()
