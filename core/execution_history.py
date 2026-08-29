"""
Execution history for AI Command Center.

Stores immutable-style historical snapshots of execution
records for later inspection, auditing, and analytics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutionHistoryRecord:
    """Historical snapshot of an execution."""

    execution_id: str
    status: str

    task_id: str | None = None

    output: Any = None

    error_code: str | None = None
    error_message: str | None = None

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class ExecutionHistory:
    """Thread-safe historical execution store."""

    _TERMINAL_STATUSES = frozenset(
        {
            "completed",
            "failed",
            "cancelled",
        }
    )

    def __init__(self) -> None:
        self._records: dict[
            str,
            ExecutionHistoryRecord,
        ] = {}

        self._lock = RLock()

    def record(
        self,
        execution_id: str,
        *,
        status: str,
        task_id: str | None = None,
        output: Any = None,
        error_code: str | None = None,
        error_message: str | None = None,
        metadata: dict[str, object] | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> ExecutionHistoryRecord:
        """Record a terminal execution snapshot."""

        normalized_id = execution_id.strip()
        normalized_status = status.strip()

        if not normalized_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        if normalized_status not in (
            self._TERMINAL_STATUSES
        ):
            raise ValueError(
                (
                    "Only terminal execution statuses "
                    "can be recorded."
                )
            )

        with self._lock:
            if normalized_id in self._records:
                raise ValueError(
                    (
                        "Execution history already contains "
                        f"{normalized_id}"
                    )
                )

            record = ExecutionHistoryRecord(
                execution_id=normalized_id,
                status=normalized_status,
                task_id=task_id,
                output=output,
                error_code=error_code,
                error_message=error_message,
                metadata=dict(
                    metadata or {}
                ),
                started_at=started_at,
                completed_at=completed_at,
            )

            self._records[
                normalized_id
            ] = record

            return record

    def get(
        self,
        execution_id: str,
    ) -> ExecutionHistoryRecord | None:
        """Return a historical execution record."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            return self._records.get(
                normalized_id
            )

    def list_all(
        self,
    ) -> tuple[ExecutionHistoryRecord, ...]:
        """Return all historical records."""

        with self._lock:
            return tuple(
                self._records.values()
            )

    def list_by_status(
        self,
        status: str,
    ) -> tuple[ExecutionHistoryRecord, ...]:
        """Return records matching a status."""

        normalized_status = status.strip()

        if not normalized_status:
            return ()

        with self._lock:
            return tuple(
                record
                for record in self._records.values()
                if record.status
                == normalized_status
            )

    def list_by_task(
        self,
        task_id: str,
    ) -> tuple[ExecutionHistoryRecord, ...]:
        """Return records belonging to a task."""

        normalized_task_id = task_id.strip()

        if not normalized_task_id:
            return ()

        with self._lock:
            return tuple(
                record
                for record in self._records.values()
                if record.task_id
                == normalized_task_id
            )

    def count(self) -> int:
        """Return total historical records."""

        with self._lock:
            return len(
                self._records
            )

    def remove(
        self,
        execution_id: str,
    ) -> bool:
        """Remove one historical record."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            return (
                self._records.pop(
                    normalized_id,
                    None,
                )
                is not None
            )

    def clear(self) -> int:
        """Remove all historical records."""

        with self._lock:
            count = len(
                self._records
            )

            self._records.clear()

            return count