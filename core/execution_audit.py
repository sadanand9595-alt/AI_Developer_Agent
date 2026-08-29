"""
Execution audit trail for AI Command Center.

Provides an immutable-style audit record for execution
lifecycle events and supports querying the audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from core.execution_event import ExecutionEvent


@dataclass(frozen=True, slots=True)
class ExecutionAuditRecord:
    """Immutable audit record for an execution event."""

    execution_id: str
    event_type: str

    task_id: str | None = None
    step_name: str | None = None

    data: Any = None

    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class ExecutionAudit:
    """Thread-safe execution audit trail."""

    def __init__(self) -> None:
        self._records: list[
            ExecutionAuditRecord
        ] = []

        self._lock = RLock()

    def record(
        self,
        event: ExecutionEvent,
    ) -> ExecutionAuditRecord:
        """Record an execution event."""

        if not isinstance(
            event,
            ExecutionEvent,
        ):
            raise TypeError(
                "Expected an ExecutionEvent instance."
            )

        record = ExecutionAuditRecord(
            execution_id=event.execution_id,
            event_type=event.event_type,
            task_id=event.task_id,
            step_name=event.step_name,
            data=event.data,
        )

        with self._lock:
            self._records.append(
                record
            )

        return record

    def record_values(
        self,
        *,
        execution_id: str,
        event_type: str,
        task_id: str | None = None,
        step_name: str | None = None,
        data: Any = None,
    ) -> ExecutionAuditRecord:
        """Record an audit entry directly from values."""

        normalized_execution_id = (
            execution_id.strip()
        )

        normalized_event_type = (
            event_type.strip()
        )

        if not normalized_execution_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        if not normalized_event_type:
            raise ValueError(
                "Event type cannot be empty."
            )

        record = ExecutionAuditRecord(
            execution_id=normalized_execution_id,
            event_type=normalized_event_type,
            task_id=task_id,
            step_name=step_name,
            data=data,
        )

        with self._lock:
            self._records.append(
                record
            )

        return record

    def list_all(
        self,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return the complete audit trail."""

        with self._lock:
            return tuple(
                self._records
            )

    def list_by_execution(
        self,
        execution_id: str,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return audit records for one execution."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return ()

        with self._lock:
            return tuple(
                record
                for record in self._records
                if record.execution_id
                == normalized_id
            )

    def list_by_event_type(
        self,
        event_type: str,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return audit records for an event type."""

        normalized_type = event_type.strip()

        if not normalized_type:
            return ()

        with self._lock:
            return tuple(
                record
                for record in self._records
                if record.event_type
                == normalized_type
            )

    def list_by_task(
        self,
        task_id: str,
    ) -> tuple[ExecutionAuditRecord, ...]:
        """Return audit records for a task."""

        normalized_task_id = task_id.strip()

        if not normalized_task_id:
            return ()

        with self._lock:
            return tuple(
                record
                for record in self._records
                if record.task_id
                == normalized_task_id
            )

    def count(self) -> int:
        """Return total audit records."""

        with self._lock:
            return len(
                self._records
            )

    def clear(self) -> int:
        """Clear the audit trail."""

        with self._lock:
            count = len(
                self._records
            )

            self._records.clear()

            return count