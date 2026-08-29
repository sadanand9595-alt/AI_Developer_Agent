"""
Application-facing execution audit service.

Provides a controlled service boundary for recording and
querying execution audit records.
"""

from __future__ import annotations

from typing import Any

from core.execution_audit import (
    ExecutionAudit,
    ExecutionAuditRecord,
)
from core.execution_event import ExecutionEvent


class ExecutionAuditService:
    """Service facade over the execution audit repository."""

    def __init__(
        self,
        audit: ExecutionAudit,
    ) -> None:
        if not isinstance(
            audit,
            ExecutionAudit,
        ):
            raise TypeError(
                "Expected an ExecutionAudit instance."
            )

        self._audit = audit

    def record_event(
        self,
        event: ExecutionEvent,
    ) -> ExecutionAuditRecord:
        """Record an execution event."""

        return self._audit.record(
            event
        )

    def record(
        self,
        *,
        execution_id: str,
        event_type: str,
        task_id: str | None = None,
        step_name: str | None = None,
        data: Any = None,
    ) -> ExecutionAuditRecord:
        """Record an audit entry from structured values."""

        return self._audit.record_values(
            execution_id=execution_id,
            event_type=event_type,
            task_id=task_id,
            step_name=step_name,
            data=data,
        )

    def get_execution(
        self,
        execution_id: str,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return the complete audit trail for an execution."""

        return self._audit.list_by_execution(
            execution_id
        )

    def get_task(
        self,
        task_id: str,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return audit records belonging to a task."""

        return self._audit.list_by_task(
            task_id
        )

    def get_event_type(
        self,
        event_type: str,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return audit records for an event type."""

        return self._audit.list_by_event_type(
            event_type
        )

    def list_all(
        self,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return the complete audit trail."""

        return self._audit.list_all()

    def count(self) -> int:
        """Return the number of audit records."""

        return self._audit.count()

    def clear(self) -> int:
        """Clear the audit trail."""

        return self._audit.clear()