from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List


class GitTools:
    """Production-quality Git helpers for commit, branch, diff, history, and staging."""

    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path).resolve()

    def _run(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip()

    def status(self) -> str:
        return self._run("status", "--short")

    def add(self, path: str | None = None) -> str:
        if path:
            return self._run("add", str(path))
        return self._run("add", "-A")

    def commit(self, message: str) -> str:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.stdout + result.stderr).strip()

    def branch(self, name: str | None = None) -> str:
        if name:
            return self._run("checkout", "-b", name)
        return self._run("branch", "--show-current")

    def diff(self, path: str | None = None) -> str:
        if path:
            return self._run("diff", "--", str(path))
        return self._run("diff")

    def history(self, limit: int = 10) -> str:
        return self._run("log", f"--max-count={limit}", "--oneline")

    def unstage(self, path: str | None = None) -> str:
        if path:
            return self._run("reset", "HEAD", "--", str(path))
        return self._run("reset", "HEAD")
