"""
Task repository for AI Command Center.

Provides persistence operations for AI tasks.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from core.types import TaskStatus
from database.models.task import Task


DEFAULT_LEASE_TTL_SECONDS = 300


class TaskRepository:
    """Persistence operations for tasks."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: str,
        title: str,
        description: str,
        conversation_id: str | None = None,
        priority: int = 0,
    ) -> Task:
        """Create and persist a new task."""

        normalized_title = title.strip()
        normalized_description = description.strip()

        if not normalized_title:
            raise ValueError("Task title cannot be empty.")

        if not normalized_description:
            raise ValueError(
                "Task description cannot be empty."
            )

        if priority < 0:
            raise ValueError(
                "Task priority cannot be negative."
            )

        task = Task(
            user_id=user_id,
            conversation_id=conversation_id,
            title=normalized_title,
            description=normalized_description,
            priority=priority,
            status=TaskStatus.PENDING.value,
        )

        self._session.add(task)
        self._session.flush()

        return task

    def get_by_id(
        self,
        task_id: str,
    ) -> Task | None:
        """Return a task by ID."""

        statement = select(Task).where(
            Task.id == task_id
        )

        return self._session.scalar(statement)

    def list_by_user(
        self,
        user_id: str,
    ) -> list[Task]:
        """Return tasks belonging to a user."""

        statement = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
        )

        return list(
            self._session.scalars(statement).all()
        )

    def list_pending(self) -> list[Task]:
        """Return tasks waiting to be processed."""

        statement = (
            select(Task)
            .where(
                Task.status == TaskStatus.PENDING.value
            )
            .order_by(
                Task.priority.desc(),
                Task.created_at.asc(),
            )
        )

        return list(
            self._session.scalars(statement).all()
        )

    def _normalize_execution_id(
        self,
        execution_id: str | None,
    ) -> str | None:
        """Return a normalized execution ID or None."""

        if isinstance(execution_id, str):
            normalized = execution_id.strip()
            return normalized or None

        return None

    def _normalize_lease_owner_id(
        self,
        lease_owner_id: str | None,
    ) -> str | None:
        """Return a normalized lease owner ID or None."""

        if isinstance(lease_owner_id, str):
            normalized = lease_owner_id.strip()
            return normalized or None

        return None

    def mark_started(
        self,
        task: Task,
        execution_id: str | None = None,
        *,
        lease_owner_id: str | None = None,
        lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
    ) -> Task:
        """Mark a task as started atomically."""

        if task.status in (
            TaskStatus.RUNNING.value,
            TaskStatus.COMPLETED.value,
        ):
            raise ValueError(
                "Cannot start a task with status "
                f"{task.status!r}."
            )

        normalized_execution_id = (
            self._normalize_execution_id(execution_id)
            or self._normalize_execution_id(task.execution_id)
            or str(uuid4())
        )
        normalized_lease_owner_id = (
            self._normalize_lease_owner_id(lease_owner_id)
            or self._normalize_lease_owner_id(task.lease_owner_id)
            or normalized_execution_id
        )
        if normalized_lease_owner_id != normalized_execution_id:
            raise ValueError(
                "lease_owner_id must match execution_id when starting a task."
            )

        now = datetime.now(timezone.utc)
        lease_expires_at = now + timedelta(
            seconds=max(0, int(lease_ttl_seconds))
        )

        statement = (
            update(Task)
            .where(Task.id == task.id)
            .where(
                Task.status.in_(
                    [
                        TaskStatus.PENDING.value,
                        TaskStatus.FAILED.value,
                    ]
                )
            )
            .values(
                status=TaskStatus.RUNNING.value,
                execution_id=normalized_execution_id,
                lease_owner_id=normalized_lease_owner_id,
                started_at=now,
                updated_at=now,
                last_heartbeat_at=now,
                lease_expires_at=lease_expires_at,
            )
        )

        result = self._session.execute(statement)

        if result.rowcount != 1:
            raise ValueError(
                "Task is not eligible to start: "
                f"{task.id}"
            )

        task.status = TaskStatus.RUNNING.value
        task.started_at = now
        task.execution_id = normalized_execution_id
        task.lease_owner_id = normalized_lease_owner_id
        task.updated_at = now
        task.last_heartbeat_at = now
        task.lease_expires_at = lease_expires_at
        self._session.flush()

        return task

    def heartbeat(
        self,
        task: Task,
        execution_id: str | None = None,
        *,
        lease_owner_id: str | None = None,
        lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
    ) -> Task:
        """Extend the lease for the current execution owner."""

        normalized_execution_id = (
            self._normalize_execution_id(execution_id)
            or self._normalize_execution_id(task.execution_id)
        )
        normalized_lease_owner_id = (
            self._normalize_lease_owner_id(lease_owner_id)
            or self._normalize_lease_owner_id(task.lease_owner_id)
        )

        if normalized_execution_id is None:
            raise ValueError(
                "Task execution_id is required for heartbeat."
            )
        if normalized_lease_owner_id is None:
            raise ValueError(
                "Task lease_owner_id is required for heartbeat."
            )
        if normalized_lease_owner_id != normalized_execution_id:
            raise ValueError(
                "lease_owner_id must match execution_id for heartbeat."
            )

        if task.status != TaskStatus.RUNNING.value:
            raise ValueError(
                "Only a running task can heartbeat."
            )

        now = datetime.now(timezone.utc)
        lease_expires_at = now + timedelta(
            seconds=max(0, int(lease_ttl_seconds))
        )

        statement = (
            update(Task)
            .where(Task.id == task.id)
            .where(Task.status == TaskStatus.RUNNING.value)
            .where(Task.execution_id == normalized_execution_id)
        )
        if normalized_lease_owner_id is not None:
            statement = statement.where(
                Task.lease_owner_id == normalized_lease_owner_id
            )

        statement = statement.values(
            last_heartbeat_at=now,
            lease_expires_at=lease_expires_at,
            updated_at=now,
        )

        result = self._session.execute(statement)

        if result.rowcount != 1:
            raise ValueError(
                "Execution does not own the active task lease: "
                f"{task.id}"
            )

        task.lease_owner_id = normalized_lease_owner_id
        task.last_heartbeat_at = now
        task.lease_expires_at = lease_expires_at
        task.updated_at = now
        self._session.flush()

        return task

    def mark_completed(
        self,
        task: Task,
        result: dict | None = None,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Mark a task as completed only by the owning execution."""

        normalized_execution_id = (
            self._normalize_execution_id(execution_id)
            or self._normalize_execution_id(task.execution_id)
        )
        normalized_lease_owner_id = (
            self._normalize_lease_owner_id(lease_owner_id)
            or self._normalize_lease_owner_id(task.lease_owner_id)
        )

        if normalized_execution_id is None:
            raise ValueError(
                "Task execution_id is required before completion."
            )
        if normalized_lease_owner_id is None:
            raise ValueError(
                "Task lease_owner_id is required before completion."
            )
        if normalized_lease_owner_id != normalized_execution_id:
            raise ValueError(
                "lease_owner_id must match execution_id before completion."
            )

        now = datetime.now(timezone.utc)

        statement = (
            update(Task)
            .where(Task.id == task.id)
            .where(Task.status == TaskStatus.RUNNING.value)
            .where(Task.execution_id == normalized_execution_id)
        )
        if normalized_lease_owner_id is not None:
            statement = statement.where(
                Task.lease_owner_id == normalized_lease_owner_id
            )

        statement = statement.values(
            status=TaskStatus.COMPLETED.value,
            result_json=result,
            error_json=None,
            completed_at=now,
            updated_at=now,
            lease_owner_id=None,
            lease_expires_at=None,
            last_heartbeat_at=None,
        )

        result_obj = self._session.execute(statement)

        if result_obj.rowcount != 1:
            raise ValueError(
                "Task is not eligible to complete with execution "
                f"ownership: {task.id}"
            )

        task.status = TaskStatus.COMPLETED.value
        task.result_json = result
        task.error_json = None
        task.completed_at = now
        task.updated_at = now
        task.lease_owner_id = None
        task.lease_expires_at = None
        task.last_heartbeat_at = None
        self._session.flush()

        return task

    def mark_failed(
        self,
        task: Task,
        error: dict | None = None,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Mark a task as failed only by the owning execution."""

        normalized_execution_id = (
            self._normalize_execution_id(execution_id)
            or self._normalize_execution_id(task.execution_id)
        )
        normalized_lease_owner_id = (
            self._normalize_lease_owner_id(lease_owner_id)
            or self._normalize_lease_owner_id(task.lease_owner_id)
        )

        if normalized_execution_id is None:
            raise ValueError(
                "Task execution_id is required before failure."
            )
        if normalized_lease_owner_id is None:
            raise ValueError(
                "Task lease_owner_id is required before failure."
            )
        if normalized_lease_owner_id != normalized_execution_id:
            raise ValueError(
                "lease_owner_id must match execution_id before failure."
            )

        now = datetime.now(timezone.utc)

        statement = (
            update(Task)
            .where(Task.id == task.id)
            .where(Task.status == TaskStatus.RUNNING.value)
            .where(Task.execution_id == normalized_execution_id)
        )
        if normalized_lease_owner_id is not None:
            statement = statement.where(
                Task.lease_owner_id == normalized_lease_owner_id
            )

        statement = statement.values(
            status=TaskStatus.FAILED.value,
            result_json=None,
            error_json=error,
            updated_at=now,
            lease_owner_id=None,
            lease_expires_at=None,
            last_heartbeat_at=None,
        )

        result_obj = self._session.execute(statement)

        if result_obj.rowcount != 1:
            raise ValueError(
                "Task is not eligible to fail with execution "
                f"ownership: {task.id}"
            )

        task.status = TaskStatus.FAILED.value
        task.result_json = None
        task.error_json = error
        task.updated_at = now
        task.lease_owner_id = None
        task.lease_expires_at = None
        task.last_heartbeat_at = None
        self._session.flush()

        return task

    def reconcile_expired_running_tasks(
        self,
        *,
        now: datetime | None = None,
    ) -> int:
        """Fail RUNNING tasks whose durable lease has expired."""

        reference_time = now or datetime.now(timezone.utc)
        error_payload = {
            "code": "TASK_LEASE_EXPIRED",
            "message": (
                "Execution lease expired after process crash or restart; "
                "the task must be retried."
            ),
        }

        statement = (
            update(Task)
            .where(Task.status == TaskStatus.RUNNING.value)
            .where(Task.lease_expires_at.is_not(None))
            .where(Task.lease_expires_at <= reference_time)
            .values(
                status=TaskStatus.FAILED.value,
                result_json=None,
                error_json=error_payload,
                updated_at=reference_time,
                lease_owner_id=None,
                lease_expires_at=None,
                last_heartbeat_at=None,
            )
        )

        result = self._session.execute(statement)
        self._session.flush()
        return int(result.rowcount or 0)

    def increment_retry(
        self,
        task: Task,
    ) -> Task:
        """Increment the task retry counter."""

        task.increment_retry()
        self._session.flush()

        return task