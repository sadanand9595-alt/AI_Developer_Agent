"""
Unified execution runtime for AI Command Center.

Coordinates execution lifecycle management, live monitoring,
and audit recording behind a single runtime boundary.
"""

from __future__ import annotations

from core.execution_audit import ExecutionAudit
from core.execution_audit_service import ExecutionAuditService
from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from core.execution_event_bus import ExecutionEventBus
from core.execution_manager import (
    ExecutionManager,
    ExecutionRecord,
)
from core.execution_monitor import ExecutionMonitor
from core.execution_tracker import ExecutionProgress, ExecutionTracker


class ExecutionRuntime:
    """Unified runtime coordinator for execution state."""

    def __init__(
        self,
        manager: ExecutionManager | None = None,
        event_bus: ExecutionEventBus | None = None,
        audit_service: ExecutionAuditService | None = None,
    ) -> None:
        self._manager = (
            manager
            if manager is not None
            else ExecutionManager()
        )

        self._event_bus = (
            event_bus
            if event_bus is not None
            else ExecutionEventBus()
        )

        self._audit_service = (
            audit_service
            if audit_service is not None
            else ExecutionAuditService(
                ExecutionAudit()
            )
        )

        self._monitor = ExecutionMonitor(
            tracker=ExecutionTracker(),
            event_bus=self._event_bus,
        )

        self._event_bus.subscribe(
            self._audit_event,
        )

    def start(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        total_steps: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Start a new execution runtime."""

        record = self._manager.start(
            execution_id,
            task_id=task_id,
            metadata=metadata,
        )

        self._monitor.start(
            execution_id,
            task_id=task_id,
            total_steps=total_steps,
        )

        return record

    def start_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Start an execution step."""

        return self._monitor.start_step(
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

        progress = self._monitor.complete_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

        if progress.status == "completed":
            self._manager.complete(
                execution_id,
            )

        return progress

    def complete(
        self,
        execution_id: str,
        *,
        output: object = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Complete an execution."""

        record = self._manager.complete(
            execution_id,
            output=output,
            metadata=metadata,
        )

        self._event_bus.publish(
            ExecutionEvent.create(
                event_type=ExecutionEventType.COMPLETED,
                execution_id=execution_id,
                task_id=record.task_id,
                data={
                    "output": output,
                },
            )
        )

        return record

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

        record = self._manager.fail(
            execution_id,
            error_code=error_code,
            error_message=error_message,
            metadata=metadata,
        )

        self._monitor.fail(
            execution_id,
            task_id=record.task_id,
            step_name=step_name,
            error_code=error_code,
            error_message=error_message,
        )

        return record

    def cancel(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Cancel an execution."""

        record = self._manager.cancel(
            execution_id,
            metadata=metadata,
        )

        self._monitor.cancel(
            execution_id,
            task_id=record.task_id,
        )

        return record

    def get(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        """Return execution lifecycle state."""

        return self._manager.get(
            execution_id
        )

    def get_progress(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """Return live execution progress."""

        return self._monitor.get_progress(
            execution_id
        )

    def get_observation(
        self,
        execution_id: str,
    ):
        """Return observed execution state."""

        return self._monitor.get_observation(
            execution_id
        )

    def get_audit(
        self,
        execution_id: str,
    ):
        """Return audit records for an execution."""

        return self._audit_service.get_execution(
            execution_id
        )

    def active(self) -> tuple[ExecutionRecord, ...]:
        """Return active execution records."""

        return self._manager.active()

    def active_count(self) -> int:
        """Return active execution count."""

        return self._manager.active_count()

    def audit_count(self) -> int:
        """Return total audit records."""

        return self._audit_service.count()

    def close(self) -> None:
        """Release runtime subscriptions."""

        self._event_bus.unsubscribe(
            self._audit_event
        )

        self._monitor.close()

    def _audit_event(
        self,
        event: ExecutionEvent,
    ) -> None:
        """Persist an execution event into the audit trail."""

        self._audit_service.record_event(
            event
        )
