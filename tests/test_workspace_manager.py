from pathlib import Path

from core.workspace_manager import WorkspaceManager


def test_workspace_manager_discovers_and_reads_files(tmp_path: Path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    sample = workspace / "sample.py"
    sample.write_text("print('hello')\n", encoding="utf-8")

    manager = WorkspaceManager(workspace)

    files = manager.discover_files()
    assert any(file_path == "sample.py" for file_path in files)

    content = manager.read_file(sample)
    assert content == "print('hello')\n"
