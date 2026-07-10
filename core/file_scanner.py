"""
==========================================================
GEETA AI IDE
File Scanner
Version : 2.3.0
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import logging


logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".json",
    ".html",
    ".css",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
}


IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
}


@dataclass(slots=True)
class FileInfo:
    path: Path
    relative_path: str
    file_name: str
    extension: str
    size: int
    line_count: int
    modified_time: float


class FileScanner:
    """
    Recursively scans a project directory and returns
    metadata for supported source files.
    """

    def __init__(self, workspace_path: str | Path):

        self.workspace = Path(workspace_path).resolve()

        if not self.workspace.exists():
            raise FileNotFoundError(self.workspace)

    # ---------------------------------------------------------

    def scan(self) -> list[FileInfo]:

        logger.info("Scanning project: %s", self.workspace)

        files: list[FileInfo] = []

        for file in self._iter_files():

            try:
                files.append(self._build_file_info(file))

            except Exception as exc:

                logger.warning(
                    "Failed to scan %s : %s",
                    file,
                    exc
                )

        logger.info("Found %d supported files", len(files))

        return files

    # ---------------------------------------------------------

    def _iter_files(self) -> Iterator[Path]:

        for path in self.workspace.rglob("*"):

            if not path.is_file():
                continue

            if self._is_ignored(path):
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            yield path

    # ---------------------------------------------------------

    def _is_ignored(self, path: Path) -> bool:

        return any(
            part in IGNORED_DIRECTORIES
            for part in path.parts
        )

    # ---------------------------------------------------------

    def _build_file_info(self, file: Path) -> FileInfo:

        stat = file.stat()

        try:

            with file.open(
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                line_count = sum(1 for _ in f)

        except Exception:

            line_count = 0

        return FileInfo(

            path=file,

            relative_path=str(
                file.relative_to(self.workspace)
            ),

            file_name=file.name,

            extension=file.suffix.lower(),

            size=stat.st_size,

            line_count=line_count,

            modified_time=stat.st_mtime,
        )