from __future__ import annotations

from pathlib import Path
from typing import List


class CodeActions:
    """Provide lightweight code-action suggestions based on the current file contents."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()

    def suggest(self, file_path: str | Path) -> List[str]:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace / path
        text = path.read_text(encoding="utf-8", errors="ignore")
        suggestions: List[str] = []
        if "def " in text:
            suggestions.append("Extract function")
        if "class " in text:
            suggestions.append("Inspect class")
        if "import " in text:
            suggestions.append("Review imports")
        return suggestions
