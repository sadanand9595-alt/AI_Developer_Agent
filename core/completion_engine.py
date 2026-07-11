from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(slots=True)
class CompletionItem:
    text: str
    kind: str = "keyword"


class CompletionEngine:
    """Simple local completion engine with keyword and symbol suggestions."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()

    def complete(self, file_path: str | Path, line: int, column: int) -> List[CompletionItem]:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        suggestions = [CompletionItem("print"), CompletionItem("return"), CompletionItem("def")]
        for token in self._extract_symbols(content):
            suggestions.append(CompletionItem(token, kind="symbol"))
        return suggestions

    def _extract_symbols(self, content: str) -> List[str]:
        symbols = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class ") or "=" in stripped:
                if "=" in stripped:
                    symbols.append(stripped.split("=", 1)[0].strip())
                else:
                    symbols.append(stripped.split()[1])
        return symbols
