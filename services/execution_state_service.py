"""
Execution state service for AI Command Center.

Synchronizes task state with the outcome of controlled
agent execution.
"""

from __future__ import annotations

from core.lifecycle import TaskLifecycle
from core.result import Result
from core.types import TaskStatus
from database.models.task import Task
from database.repositories.task_repository import TaskRepository


class ExecutionStateService:
    """Manage task state after execution results."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    @staticmethod
    def _validate_transition(
        task: Task,
        target: TaskStatus,
    ) -> None:
        """Reject invalid lifecycle transitions before repository calls."""

        current_value = getattr(task, "status", None)

        try:
            current = TaskStatus(current_value)
        except (ValueError, TypeError):
            raise ValueError(
                f"Unknown task status: {current_value!r}"
            ) from None

        TaskLifecycle.transition(current, target)

    def mark_success(
        self,
        task: Task,
        result: dict | None = None,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Result[Task]:
        """Mark a running task as completed."""

        try:
            self._validate_transition(
                task,
                TaskStatus.COMPLETED,
            )

            self._repository.mark_completed(
                task,
                result,
                execution_id=execution_id,
                lease_owner_id=lease_owner_id,
            )

            return Result.ok(task)

        except Exception as exc:
            return Result.fail(
                "TASK_COMPLETION_FAILED",
                str(exc),
                details={
                    "task_id": task.id,
                    "execution_id": execution_id,
                },
            )

    def mark_failure(
        self,
        task: Task,
        error: dict | None = None,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Result[Task]:
        """Mark a running task as failed."""

        try:
            self._validate_transition(
                task,
                TaskStatus.FAILED,
            )

            self._repository.mark_failed(
                task,
                error,
                execution_id=execution_id,
                lease_owner_id=lease_owner_id,
            )

            return Result.ok(task)

        except Exception as exc:
            return Result.fail(
                "TASK_FAILURE_UPDATE_FAILED",
                str(exc),
                details={
                    "task_id": task.id,
                    "execution_id": execution_id,
                },
            )

    def increment_retry(
        self,
        task: Task,
    ) -> Result[Task]:
        """Increment the retry count without changing task status."""

        try:
            self._repository.increment_retry(task)

            return Result.ok(task)

        except Exception as exc:
            return Result.fail(
                "TASK_RETRY_UPDATE_FAILED",
                str(exc),
                details={
                    "task_id": task.id,
                },
            )

    def mark_started(
        self,
        task: Task,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Result[Task]:
        """Start a pending or failed task."""

        try:
            self._validate_transition(
                task,
                TaskStatus.RUNNING,
            )

            self._repository.mark_started(
                task,
                execution_id,
                lease_owner_id=lease_owner_id,
            )

            return Result.ok(task)

        except Exception as exc:
            return Result.fail(
                "TASK_START_FAILED",
                str(exc),
                details={
                    "task_id": task.id,
                    "execution_id": execution_id,
                },
            )
