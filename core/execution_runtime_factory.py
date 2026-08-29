"""
Execution runtime factory for AI Command Center.

Centralizes dependency construction for the execution runtime
and its application-facing service.
"""

from __future__ import annotations

from core.execution_audit import ExecutionAudit
from core.execution_audit_service import ExecutionAuditService
from core.execution_event_bus import ExecutionEventBus
from core.execution_manager import ExecutionManager
from core.execution_runtime import ExecutionRuntime
from core.execution_runtime_service import (
    ExecutionRuntimeService,
)


class ExecutionRuntimeFactory:
    """Factory for constructing execution runtime services."""

    @staticmethod
    def create() -> ExecutionRuntimeService:
        """Create a fully configured runtime service."""

        manager = ExecutionManager()

        event_bus = ExecutionEventBus()

        audit = ExecutionAudit()

        audit_service = ExecutionAuditService(
            audit
        )

        runtime = ExecutionRuntime(
            manager=manager,
            event_bus=event_bus,
            audit_service=audit_service,
        )

        return ExecutionRuntimeService(
            runtime
        )