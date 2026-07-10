from core.project_indexer import ProjectIndexer
from pathlib import Path


def test_project_indexer_persists_real_workspace_file_metadata(workspace, isolated_database):
    indexed = ProjectIndexer(workspace).build_index()

    workspace_row = isolated_database.fetchone(
        "SELECT name, root_path, total_files, indexed FROM workspace"
    )
    files = isolated_database.fetchall(
        "SELECT relative_path, language, line_count FROM files ORDER BY relative_path"
    )

    assert indexed == 4
    assert workspace_row["name"] == workspace.name
    assert workspace_row["root_path"] == str(workspace.resolve())
    assert workspace_row["total_files"] == 4
    assert workspace_row["indexed"] == 1
    assert [row["relative_path"] for row in files] == [
        "README.md",
        "settings.yaml",
        str(Path("src") / "helpers.py"),
        str(Path("src") / "main.py"),
    ]
    main = str(Path("src") / "main.py")
    assert next(row for row in files if row["relative_path"] == main)["language"] == "Python"


def test_project_indexer_rebuild_replaces_previous_file_metadata(workspace, isolated_database):
    indexer = ProjectIndexer(workspace)
    indexer.build_index()
    (workspace / "extra.txt").write_text("extra\n", encoding="utf-8")

    indexed = indexer.build_index()
    count = isolated_database.fetchone("SELECT COUNT(*) AS total FROM files")

    assert indexed == 5
    assert count["total"] == 5
