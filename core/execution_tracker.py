"""
Execution tracker for AI Command Center.

Tracks live execution progress, current step, completed steps,
and execution status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock


@dataclass(slots=True)
class ExecutionProgress:
    """Current progress state of an execution."""

    execution_id: str
    total_steps: int = 0
    completed_steps: int = 0

    current_step: str | None = None
    status: str = "pending"

    started_at: datetime | None = None
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @property
    def progress_percent(self) -> float:
        """Return completion percentage."""

        if self.total_steps <= 0:
            return 0.0

        completed = min(
            self.completed_steps,
            self.total_steps,
        )

        return round(
            (completed / self.total_steps) * 100,
            2,
        )


class ExecutionTracker:
    """Thread-safe execution progress tracker."""

    def __init__(self) -> None:
        self._executions: dict[
            str,
            ExecutionProgress,
        ] = {}

        self._lock = RLock()

    def start(
        self,
        execution_id: str,
        *,
        total_steps: int,
    ) -> ExecutionProgress:
        """Start tracking an execution."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        if total_steps < 0:
            raise ValueError(
                "Total steps cannot be negative."
            )

        with self._lock:
            if normalized_id in self._executions:
                raise ValueError(
                    f"Execution already tracked: {normalized_id}"
                )

            now = datetime.now(
                timezone.utc
            )

            progress = ExecutionProgress(
                execution_id=normalized_id,
                total_steps=total_steps,
                completed_steps=0,
                current_step=None,
                status="running",
                started_at=now,
                updated_at=now,
            )

            self._executions[
                normalized_id
            ] = progress

            return progress

    def get(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """Return tracked execution progress."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            return self._executions.get(
                normalized_id
            )

    def start_step(
        self,
        execution_id: str,
        step_name: str,
    ) -> ExecutionProgress:
        """Mark a step as currently executing."""

        normalized_step = step_name.strip()

        if not normalized_step:
            raise ValueError(
                "Step name cannot be empty."
            )

        progress = self._require(
            execution_id
        )

        with self._lock:
            progress.current_step = normalized_step
            progress.status = "running"
            progress.updated_at = datetime.now(
                timezone.utc
            )

            return progress

    def complete_step(
        self,
        execution_id: str,
        step_name: str | None = None,
    ) -> ExecutionProgress:
        """Mark the current step as completed."""

        progress = self._require(
            execution_id
        )

        with self._lock:
            if (
                step_name is not None
                and step_name.strip()
            ):
                progress.current_step = (
                    step_name.strip()
                )

            if (
                progress.completed_steps
                >= progress.total_steps
                and progress.total_steps > 0
            ):
                raise ValueError(
                    "All execution steps are already completed."
                )

            progress.completed_steps += 1

            if (
                progress.total_steps > 0
                and progress.completed_steps
                >= progress.total_steps
            ):
                progress.completed_steps = (
                    progress.total_steps
                )
                progress.current_step = None
                progress.status = "completed"

            progress.updated_at = datetime.now(
                timezone.utc
            )

            return progress

    def complete(
        self,
        execution_id: str,
    ) -> ExecutionProgress:
        """
        Mark an execution as completed without a driving step.

        Used when an execution completes without progressing
        through individually tracked steps (e.g. zero-step plans),
        so tracked progress stays consistent with the execution's
        lifecycle status.
        """

        progress = self._require(
            execution_id
        )

        with self._lock:
            progress.completed_steps = (
                progress.total_steps
            )
            progress.current_step = None
            progress.status = "completed"
            progress.updated_at = datetime.now(
                timezone.utc
            )

            return progress

    def fail(
        self,
        execution_id: str,
        *,
        step_name: str | None = None,
    ) -> ExecutionProgress:
        """Mark an execution as failed."""

        progress = self._require(
            execution_id
        )

        with self._lock:
            if step_name is not None:
                normalized_step = step_name.strip()

                if normalized_step:
                    progress.current_step = (
                        normalized_step
                    )

            progress.status = "failed"
            progress.updated_at = datetime.now(
                timezone.utc
            )

            return progress

    def cancel(
        self,
        execution_id: str,
    ) -> ExecutionProgress:
        """Mark an execution as cancelled."""

        progress = self._require(
            execution_id
        )

        with self._lock:
            progress.status = "cancelled"
            progress.updated_at = datetime.now(
                timezone.utc
            )

            return progress

    def active(
        self,
    ) -> tuple[ExecutionProgress, ...]:
        """Return currently active executions."""

        with self._lock:
            return tuple(
                progress
                for progress in self._executions.values()
                if progress.status
                in {
                    "running",
                    "pending",
                }
            )

    def count(self) -> int:
        """Return number of tracked executions."""

        with self._lock:
            return len(
                self._executions
            )

    def remove(
        self,
        execution_id: str,
    ) -> bool:
        """Remove a tracked execution."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            return (
                self._executions.pop(
                    normalized_id,
                    None,
                )
                is not None
            )

    def clear_finished(self) -> int:
        """Remove completed, failed, and cancelled executions."""

        terminal_statuses = {
            "completed",
            "failed",
            "cancelled",
        }

        with self._lock:
            removable = [
                execution_id
                for execution_id, progress
                in self._executions.items()
                if progress.status
                in terminal_statuses
            ]

            for execution_id in removable:
                del self._executions[
                    execution_id
                ]

            return len(removable)

    def _require(
        self,
        execution_id: str,
    ) -> ExecutionProgress:
        """Return a tracked execution or raise."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        with self._lock:
            progress = self._executions.get(
                normalized_id
            )

            if progress is None:
                raise KeyError(
                    f"Execution not found: {normalized_id}"
                )

            return progress