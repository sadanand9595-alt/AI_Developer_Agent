from __future__ import annotations

from pathlib import Path


class LanguageSupport:
    """Multi-language detection for the editor and tooling surfaces."""

    _mapping = {
        ".py": "Python",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
    }

    def detect(self, file_path: str | Path) -> str:
        suffix = Path(file_path).suffix.lower()
        return self._mapping.get(suffix, "Plain Text")
