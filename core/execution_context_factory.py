"""
Execution context factory for AI Command Center.

Centralizes construction of execution-context services.
"""

from __future__ import annotations

from core.execution_context_service import (
    ExecutionContextService,
)


class ExecutionContextFactory:
    """Factory for creating execution context services."""

    @staticmethod
    def create() -> ExecutionContextService:
        """Create a fully configured context service."""

        return ExecutionContextService()


__all__ = [
    "ExecutionContextFactory",
]