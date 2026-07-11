from __future__ import annotations


class AIDebugger:
    """AI-assisted debugging helpers for exception explanation and repair suggestions."""

    def explain_exception(self, error: str) -> str:
        if "NameError" in error:
            return "NameError indicates a variable or symbol is referenced before it is defined."
        return f"Unhandled exception: {error}"

    def auto_fix(self, code: str, error: str) -> str:
        if "NameError" in error:
            return f"Define the missing symbol before use in: {code}"
        return f"Review the code around: {code}"

    def one_click_repair(self, code: str, error: str) -> str:
        return self.auto_fix(code, error)
