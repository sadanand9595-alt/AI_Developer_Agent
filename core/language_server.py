from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(slots=True)
class LSPMessage:
    kind: str
    message: str


class LanguageServer:
    """A lightweight LSP-compatible server facade for diagnostics and symbol requests."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()

    def capabilities(self) -> dict[str, object]:
        return {"hover": True, "completion": True, "diagnostics": True}

    def hover(self, path: str | Path, line: int, column: int) -> List[LSPMessage]:
        return [LSPMessage("info", f"Hover for {Path(path).name} at {line}:{column}")]

    def completion(self, path: str | Path, line: int, column: int) -> List[LSPMessage]:
        return [LSPMessage("completion", "def"), LSPMessage("completion", "class")]

    def diagnostics(self, path: str | Path) -> List[LSPMessage]:
        return []
