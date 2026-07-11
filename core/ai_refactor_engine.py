from __future__ import annotations


class AIRefactorEngine:
    """Lightweight refactoring suggestions for extracting helpers and improving structure."""

    def extract_method(self, code: str, name: str) -> str:
        return f"def {name}():\n    pass\n\n{code}"
