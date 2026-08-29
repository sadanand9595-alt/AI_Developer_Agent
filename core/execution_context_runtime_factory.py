"""
Factory for execution context runtime services.

Centralizes construction of the runtime management layer.
"""

from __future__ import annotations

from core.execution_context_runtime_service import (
    ExecutionContextRuntimeService,
)


class ExecutionContextRuntimeFactory:
    """Factory for creating execution runtime services."""

    @staticmethod
    def create() -> ExecutionContextRuntimeService:
        """Create an isolated runtime service."""

        return ExecutionContextRuntimeService()


__all__ = [
    "ExecutionContextRuntimeFactory",
]