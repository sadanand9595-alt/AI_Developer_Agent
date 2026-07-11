from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(slots=True)
class DiagnosticIssue:
    path: str
    line: int
    kind: str
    message: str


class DiagnosticsEngine:
    """Lightweight diagnostics engine that surfaces syntax issues and simple warnings."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()

    def analyze(self, file_path: str | Path) -> List[DiagnosticIssue]:
        path = Path(file_path)
        issues: List[DiagnosticIssue] = []
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            ast.parse(source)
        except SyntaxError as exc:
            issues.append(
                DiagnosticIssue(
                    path=str(path.relative_to(self.workspace)),
                    line=exc.lineno or 1,
                    kind="error",
                    message=str(exc),
                )
            )

        if "TODO" in source:
            issues.append(
                DiagnosticIssue(
                    path=str(path.relative_to(self.workspace)),
                    line=1,
                    kind="warning",
                    message="TODO found in source",
                )
            )

        return issues
