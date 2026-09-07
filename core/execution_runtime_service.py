"""
Application-facing execution runtime service.

Provides a controlled service boundary over the unified
ExecutionRuntime.
"""

from __future__ import annotations

from typing import Any

from core.execution_manager import ExecutionRecord
from core.execution_runtime import ExecutionRuntime
from core.execution_tracker import ExecutionProgress


class ExecutionRuntimeService:
    """Application-facing facade over ExecutionRuntime."""

    def __init__(
        self,
        runtime: ExecutionRuntime,
    ) -> None:
        if not isinstance(
            runtime,
            ExecutionRuntime,
        ):
            raise TypeError(
                "Expected an ExecutionRuntime instance."
            )

        self._runtime = runtime

    def start(
        self,
        *,
        execution_id: str,
        task_id: str | None = None,
        total_steps: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Start an execution."""

        return self._runtime.start(
            execution_id,
            task_id=task_id,
            total_steps=total_steps,
            metadata=metadata,
        )

    def start_step(
        self,
        *,
        execution_id: str,
        step_name: str,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Start an execution step."""

        return self._runtime.start_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

    def complete_step(
        self,
        *,
        execution_id: str,
        step_name: str,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Complete an execution step."""

        return self._runtime.complete_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

    def complete(
        self,
        *,
        execution_id: str,
        output: Any = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Complete an execution."""

        return self._runtime.complete(
            execution_id,
            output=output,
            metadata=metadata,
        )

    def fail(
        self,
        *,
        execution_id: str,
        error_code: str,
        error_message: str,
        step_name: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Fail an execution."""

        return self._runtime.fail(
            execution_id,
            error_code=error_code,
            error_message=error_message,
            step_name=step_name,
            metadata=metadata,
        )

    def cancel(
        self,
        *,
        execution_id: str,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Cancel an execution."""

        return self._runtime.cancel(
            execution_id,
            metadata=metadata,
        )

    def wait_for_approval(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Mark an execution as waiting for approval."""

        return self._runtime.wait_for_approval(
            execution_id,
            metadata=metadata,
        )

    def get(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        """Get execution state."""

        return self._runtime.get(
            execution_id
        )

    def get_progress(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """Get live execution progress."""

        return self._runtime.get_progress(
            execution_id
        )

    def get_observation(
        self,
        execution_id: str,
    ):
        """Get observed execution state."""

        return self._runtime.get_observation(
            execution_id
        )

    def get_audit(
        self,
        execution_id: str,
    ):
        """Get execution audit records."""

        return self._runtime.get_audit(
            execution_id
        )

    def active(
        self,
    ) -> tuple[ExecutionRecord, ...]:
        """Return active executions."""

        return self._runtime.active()

    def active_count(self) -> int:
        """Return active execution count."""

        return self._runtime.active_count()

    def audit_count(self) -> int:
        """Return total audit records."""

        return self._runtime.audit_count()

    def close(self) -> None:
        """Close the underlying runtime."""

        self._runtime.close()