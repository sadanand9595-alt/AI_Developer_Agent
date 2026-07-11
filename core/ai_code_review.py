from __future__ import annotations


class AICodeReview:
    """Lightweight AI-powered review suggestions for source code."""

    def review(self, code: str) -> list[str]:
        issues = []
        if "pass" in code:
            issues.append("Consider implementing the placeholder block.")
        if "TODO" in code:
            issues.append("TODO marker found.")
        return issues
