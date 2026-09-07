"""
Top-level execution system for AI Command Center.

Provides a single orchestration boundary for execution
coordination, lifecycle management, monitoring, registry,
and audit access.
"""

from __future__ import annotations

from core.execution_coordinator import ExecutionCoordinator
from core.execution_facade import ExecutionFacade
from core.execution_manager import ExecutionRecord
from core.execution_tracker import ExecutionProgress
from core.pipeline_context import PipelineContext
from core.result import Result


class ExecutionSystem:
    """Top-level orchestration layer for executions."""

    def __init__(
        self,
        coordinator: ExecutionCoordinator | None = None,
    ) -> None:
        if coordinator is not None and not isinstance(
            coordinator,
            ExecutionCoordinator,
        ):
            raise TypeError(
                "Expected an ExecutionCoordinator instance."
            )

        self._coordinator = (
            coordinator
            if coordinator is not None
            else ExecutionCoordinator()
        )

    def start(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        total_steps: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Start and register an execution."""

        return self._coordinator.start(
            execution_id,
            task_id=task_id,
            total_steps=total_steps,
            metadata=metadata,
        )

    def execute(
        self,
        *,
        request: str,
        steps: list[dict[str, object]],
        context: PipelineContext,
    ) -> Result[PipelineContext]:
        """Build and execute a plan through the coordinator."""

        return self._coordinator.execute(
            request=request,
            steps=steps,
            context=context,
        )

    @property
    def coordinator(self) -> ExecutionCoordinator:
        """Return the configured execution coordinator."""

        return self._coordinator

    def start_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Start an execution step."""

        return self._coordinator.start_step(
            execution_id,
            step_name,
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

        return self._coordinator.complete_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

    def complete(
        self,
        execution_id: str,
        *,
        output: object = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Complete an execution."""

        return self._coordinator.complete(
            execution_id,
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

        return self._coordinator.fail(
            execution_id,
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

        return self._coordinator.cancel(
            execution_id,
            metadata=metadata,
        )

    def get(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        """Return execution state."""

        return self._coordinator.get(
            execution_id
        )

    def get_progress(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """Return execution progress."""

        return self._coordinator.get_progress(
            execution_id
        )

    def get_observation(
        self,
        execution_id: str,
    ):
        """Return execution observation."""

        return self._coordinator.get_observation(
            execution_id
        )

    def get_audit(
        self,
        execution_id: str,
    ):
        """Return execution audit records."""

        return self._coordinator.get_audit(
            execution_id
        )

    def is_registered(
        self,
        execution_id: str,
    ) -> bool:
        """Return whether an execution is registered."""

        return self._coordinator.is_registered(
            execution_id
        )

    def registered_count(self) -> int:
        """Return number of registered executions."""

        return self._coordinator.registered_count()

    def registered_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered execution IDs."""

        return self._coordinator.registered_ids()

    def active_count(self) -> int:
        """Return active execution count."""

        return self._coordinator.active_count()

    def audit_count(self) -> int:
        """Return total audit records."""

        return self._coordinator.audit_count()

    def close(self) -> None:
        """Close the execution system."""

        self._coordinator.close()


__all__ = [
    "ExecutionSystem",
]