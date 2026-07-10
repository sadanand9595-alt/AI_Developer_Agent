"""Shared pytest fixtures for GEETA AI tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from database import database


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_TMP_DIR = REPO_ROOT / "workspace" / "tmp"
LOCAL_TMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("TMPDIR", str(LOCAL_TMP_DIR))
os.environ.setdefault("TEMP", str(LOCAL_TMP_DIR))
os.environ.setdefault("TMP", str(LOCAL_TMP_DIR))
tempfile.tempdir = str(LOCAL_TMP_DIR)

def pytest_ignore_collect(collection_path, config):
    path = Path(str(collection_path))
    return str(path).startswith(str(LOCAL_TMP_DIR)) or path.name.startswith("test_workspace_index_rejects")


def pytest_configure(config):
    config.option.pyargs = False


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create a small, representative project using real source files."""
    source = tmp_path / "src"
    source.mkdir()

    (source / "helpers.py").write_text(
        '"""Helper functions."""\n\n\ndef greeting(name: str) -> str:\n    return f"Hello, {name}"\n',
        encoding="utf-8",
    )
    (source / "main.py").write_text(
        "import os\nfrom src.helpers import greeting\n\n\nclass Application:\n"
        "    \"\"\"Application entry point.\"\"\"\n\n"
        "    def run(self, value: str) -> str:\n"
        "        return greeting(value)\n\n\n"
        "async def shutdown() -> None:\n"
        "    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Sample workspace\n", encoding="utf-8")
    (tmp_path / "settings.yaml").write_text("enabled: true\n", encoding="utf-8")

    ignored = tmp_path / ".git"
    ignored.mkdir()
    (ignored / "ignored.py").write_text("def ignored(): pass\n", encoding="utf-8")

    return tmp_path


@pytest.fixture
def isolated_database(tmp_path: Path):
    """Route the real DatabaseManager to a disposable SQLite database."""
    original = (
        database.database_dir,
        database.database_path,
        database.schema_path,
    )
    database.close()
    database.database_dir = tmp_path
    database.database_path = tmp_path / "project_index.db"
    database.schema_path = original[2]
    database.connect()
    database.initialize_database()

    try:
        yield database
    finally:
        database.close()
        database.database_dir, database.database_path, database.schema_path = original
        database.connect()
        database.initialize_database()
