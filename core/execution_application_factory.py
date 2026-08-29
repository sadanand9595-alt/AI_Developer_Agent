"""
Execution application factory for AI Command Center.

Centralizes construction of the application-facing execution
component.
"""

from __future__ import annotations

from core.execution_application import ExecutionApplication


class ExecutionApplicationFactory:
    """Factory for creating ExecutionApplication instances."""

    @staticmethod
    def create() -> ExecutionApplication:
        """Create a fully configured execution application."""

        return ExecutionApplication()


__all__ = [
    "ExecutionApplicationFactory",
]