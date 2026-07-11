from pathlib import Path
import subprocess

from tools.git_tools import GitTools


def test_git_tools_expose_core_operations(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    (repo / "file.txt").write_text("hello\n", encoding="utf-8")

    tools = GitTools(repo)
    assert tools.status() != ""
    assert tools.add("file.txt") == ""
    assert tools.unstage("file.txt") == ""
    assert tools.diff("file.txt") == ""
