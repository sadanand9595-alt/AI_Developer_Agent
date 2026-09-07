"""
Execution manager for AI Command Center.

Tracks active and completed executions and provides a
controlled lifecycle boundary around execution records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass(slots=True)
class ExecutionRecord:
    """Runtime record for a single execution."""

    execution_id: str
    task_id: str | None = None
    status: str = "running"

    output: Any = None

    error_code: str | None = None
    error_message: str | None = None

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    started_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    completed_at: datetime | None = None


class ExecutionManager:
    """Thread-safe manager for execution lifecycle records."""

    _ACTIVE_STATUS = "running"

    _TERMINAL_STATUSES = frozenset(
        {
            "completed",
            "failed",
            "cancelled",
        }
    )

    def __init__(self) -> None:
        self._executions: dict[
            str,
            ExecutionRecord,
        ] = {}

        self._lock = RLock()

    def start(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Register a new running execution."""

        if not isinstance(
            execution_id,
            str,
        ):
            raise ValueError(
                "Execution ID must be a string."
            )

        normalized_id = execution_id.strip()

        if not normalized_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        with self._lock:
            if normalized_id in self._executions:
                raise ValueError(
                    f"Execution already exists: {normalized_id}"
                )

            record = ExecutionRecord(
                execution_id=normalized_id,
                task_id=task_id,
                status=self._ACTIVE_STATUS,
                metadata=dict(
                    metadata or {}
                ),
            )

            self._executions[
                normalized_id
            ] = record

            return record

    def get(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        """Return an execution record if it exists."""

        if not isinstance(
            execution_id,
            str,
        ):
            return None

        normalized_id = execution_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            return self._executions.get(
                normalized_id
            )

    def complete(
        self,
        execution_id: str,
        *,
        output: Any = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Mark an execution as completed."""

        return self._finish(
            execution_id,
            status="completed",
            output=output,
            metadata=metadata,
        )

    def wait_for_approval(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Mark an active execution as waiting for approval."""

        with self._lock:
            record = self._executions.get(execution_id.strip())
            if record is None:
                raise KeyError(f"Execution not found: {execution_id}")
            if record.status != self._ACTIVE_STATUS:
                raise ValueError("Execution is not running.")
            record.status = "waiting_approval"
            if metadata:
                record.metadata.update(metadata)
            return record

    def fail(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Mark an execution as failed."""

        if not isinstance(
            error_code,
            str,
        ):
            raise ValueError(
                "Error code must be a string."
            )

        if not isinstance(
            error_message,
            str,
        ):
            raise ValueError(
                "Error message must be a string."
            )

        normalized_code = error_code.strip()
        normalized_message = error_message.strip()

        if not normalized_code:
            raise ValueError(
                "Error code cannot be empty."
            )

        if not normalized_message:
            raise ValueError(
                "Error message cannot be empty."
            )

        return self._finish(
            execution_id,
            status="failed",
            error_code=normalized_code,
            error_message=normalized_message,
            metadata=metadata,
        )

    def cancel(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Mark an execution as cancelled."""

        return self._finish(
            execution_id,
            status="cancelled",
            metadata=metadata,
        )

    def active(
        self,
    ) -> tuple[ExecutionRecord, ...]:
        """Return all currently running executions."""

        with self._lock:
            return tuple(
                record
                for record in self._executions.values()
                if record.status
                == self._ACTIVE_STATUS
            )

    def count(
        self,
    ) -> int:
        """Return total tracked executions."""

        with self._lock:
            return len(
                self._executions
            )

    def active_count(
        self,
    ) -> int:
        """Return number of active executions."""

        return len(
            self.active()
        )

    def clear_completed(self) -> int:
        """Remove terminal execution records."""

        with self._lock:
            removable = [
                execution_id
                for execution_id, record
                in self._executions.items()
                if record.status
                in self._TERMINAL_STATUSES
            ]

            for execution_id in removable:
                del self._executions[
                    execution_id
                ]

            return len(removable)

    def _finish(
        self,
        execution_id: str,
        *,
        status: str,
        output: Any = None,
        error_code: str | None = None,
        error_message: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Transition an execution to a terminal state."""

        if not isinstance(
            execution_id,
            str,
        ):
            raise ValueError(
                "Execution ID must be a string."
            )

        normalized_id = execution_id.strip()

        if not normalized_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        if status not in self._TERMINAL_STATUSES:
            raise ValueError(
                f"Invalid terminal status: {status}"
            )

        with self._lock:
            record = self._executions.get(
                normalized_id
            )

            if record is None:
                raise KeyError(
                    f"Execution not found: {normalized_id}"
                )

            if record.status in self._TERMINAL_STATUSES:
                raise ValueError(
                    "Execution is already in a terminal state."
                )

            record.status = status
            record.output = output
            record.error_code = error_code
            record.error_message = error_message
            record.completed_at = datetime.now(
                timezone.utc
            )

            if metadata:
                record.metadata.update(
                    metadata
                )

            return record
