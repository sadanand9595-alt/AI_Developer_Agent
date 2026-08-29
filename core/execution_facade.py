"""
Public execution facade for AI Command Center.

Provides a single high-level entry point for execution
lifecycle, progress monitoring, and audit access.
"""

from __future__ import annotations

from typing import Any

from core.execution_manager import ExecutionRecord
from core.execution_runtime_factory import (
    ExecutionRuntimeFactory,
)
from core.execution_runtime_service import (
    ExecutionRuntimeService,
)
from core.execution_tracker import ExecutionProgress


class ExecutionFacade:
    """Single public API for the execution subsystem."""

    def __init__(
        self,
        service: ExecutionRuntimeService | None = None,
    ) -> None:
        self._service = (
            service
            if service is not None
            else ExecutionRuntimeFactory.create()
        )

    def start(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        total_steps: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Start an execution."""

        return self._service.start(
            execution_id=execution_id,
            task_id=task_id,
            total_steps=total_steps,
            metadata=metadata,
        )

    def start_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Start an execution step."""

        return self._service.start_step(
            execution_id=execution_id,
            step_name=step_name,
            task_id=task_id,
        )

    def complete_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Complete an execution step."""

        return self._service.complete_step(
            execution_id=execution_id,
            step_name=step_name,
            task_id=task_id,
        )

    def complete(
        self,
        execution_id: str,
        *,
        output: Any = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Complete an execution."""

        return self._service.complete(
            execution_id=execution_id,
            output=output,
            metadata=metadata,
        )

    def fail(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        step_name: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Fail an execution."""

        return self._service.fail(
            execution_id=execution_id,
            error_code=error_code,
            error_message=error_message,
            step_name=step_name,
            metadata=metadata,
        )

    def cancel(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Cancel an execution."""

        return self._service.cancel(
            execution_id=execution_id,
            metadata=metadata,
        )

    def get(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        """Get execution state."""

        return self._service.get(
            execution_id
        )

    def get_progress(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """Get current execution progress."""

        return self._service.get_progress(
            execution_id
        )

    def get_observation(
        self,
        execution_id: str,
    ):
        """Get current execution observation."""

        return self._service.get_observation(
            execution_id
        )

    def get_audit(
        self,
        execution_id: str,
    ):
        """Get audit records for an execution."""

        return self._service.get_audit(
            execution_id
        )

    def active(
        self,
    ) -> tuple[ExecutionRecord, ...]:
        """Return active executions."""

        return self._service.active()

    def active_count(self) -> int:
        """Return active execution count."""

        return self._service.active_count()

    def audit_count(self) -> int:
        """Return total audit records."""

        return self._service.audit_count()

    def close(self) -> None:
        """Close the execution subsystem."""

        self._service.close()