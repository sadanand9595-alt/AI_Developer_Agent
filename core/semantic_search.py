from __future__ import annotations

from pathlib import Path
from typing import List

from core.file_scanner import FileScanner


class SemanticSearch:
    """Provide project-aware semantic search over file content and metadata."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()
        self.scanner = FileScanner(self.workspace)

    def search(self, query: str) -> List[str]:
        if not query:
            return []
        needle = query.lower()
        results: List[str] = []
        for info in self.scanner.scan():
            path = self.workspace / info.relative_path
            try:
                content = path.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                continue
            tokens = {token for token in content.split() if len(token) > 2}
            path_tokens = {part.lower() for part in path.parts if part.lower() not in {"", ".", ".."}}
            if needle in info.relative_path.lower() or needle in content or any(needle in token for token in tokens) or any(needle in token for token in path_tokens):
                results.append(info.relative_path)
        return results
