"""
==========================================================
GEETA AI IDE
Project Indexer
Version : 2.3.0
==========================================================

Scans the workspace and stores project metadata
into the SQLite database.
"""

from __future__ import annotations

import logging
from pathlib import Path

from core.file_scanner import FileScanner
from database import database

logger = logging.getLogger(__name__)


class ProjectIndexer:
    """
    Project Indexer

    Responsibilities
    ----------------
    • Scan workspace
    • Store file metadata
    • Update workspace info
    """

    def __init__(self, workspace_path: str | Path):

        self.workspace = Path(workspace_path).resolve()

        self.scanner = FileScanner(self.workspace)

    # ---------------------------------------------------------

    def build_index(self) -> int:
        """
        Scan the workspace and build database index.

        Returns
        -------
        int
            Number of indexed files.
        """

        logger.info("Starting project indexing...")

        files = self.scanner.scan()

        workspace_id = self._create_workspace(len(files))

        self._clear_previous_files()

        for file in files:

            self._insert_file(workspace_id, file)

        logger.info("Index Complete")

        return len(files)

    # ---------------------------------------------------------

    def _create_workspace(self, total_files: int) -> int:

        database.execute(
            """
            INSERT OR REPLACE INTO workspace
            (
                id,
                name,
                root_path,
                total_files,
                indexed
            )
            VALUES
            (
                1,
                ?,
                ?,
                ?,
                1
            )
            """,
            (
                self.workspace.name,
                str(self.workspace),
                total_files,
            ),
        )

        row = database.fetchone(
            "SELECT id FROM workspace LIMIT 1"
        )

        return row["id"]

    # ---------------------------------------------------------

    def _clear_previous_files(self):

        database.execute(
            "DELETE FROM files"
        )

    # ---------------------------------------------------------

    def _insert_file(self, workspace_id, file):

        database.execute(
            """
            INSERT INTO files
            (
                workspace_id,
                path,
                relative_path,
                file_name,
                extension,
                language,
                size,
                line_count,
                modified_time
            )

            VALUES
            (
                ?,?,?,?,?,?,?,?,?
            )
            """,
            (
                workspace_id,
                str(file.path),
                file.relative_path,
                file.file_name,
                file.extension,
                self._language(file.extension),
                file.size,
                file.line_count,
                str(file.modified_time),
            ),
        )

    # ---------------------------------------------------------

    @staticmethod
    def _language(extension: str) -> str:

        mapping = {

            ".py": "Python",

            ".js": "JavaScript",

            ".ts": "TypeScript",

            ".tsx": "TypeScript",

            ".jsx": "JavaScript",

            ".json": "JSON",

            ".html": "HTML",

            ".css": "CSS",

            ".md": "Markdown",

            ".txt": "Text",

            ".yaml": "YAML",

            ".yml": "YAML",

        }

        return mapping.get(extension.lower(), "Unknown")