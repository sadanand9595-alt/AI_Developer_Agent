from __future__ import annotations

from pathlib import Path


class RefactoringEngine:
    """Simple local refactoring helpers for extracting methods and renaming variables."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()

    def extract_method(self, file_path: str | Path, start_line: int, end_line: int, name: str) -> str:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        lines = content.splitlines()
        body = "\n".join(lines[start_line - 1:end_line])
        replacement = f"\n\ndef {name}():\n    {body.replace(chr(10), chr(10) + '    ')}\n"
        return content + replacement

    def rename_variable(self, file_path: str | Path, old_name: str, new_name: str) -> str:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        return content.replace(old_name, new_name)
