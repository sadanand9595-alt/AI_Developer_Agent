"""
Task repository for AI Command Center.

Provides persistence operations for AI tasks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from core.types import TaskStatus
from database.models.task import Task


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

    def mark_started(
        self,
        task: Task,
        execution_id: str | None = None,
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
            execution_id.strip()
            if isinstance(execution_id, str)
            else None
        )

        if normalized_execution_id is None:
            normalized_execution_id = str(
                task.execution_id or uuid4()
            )

        now = datetime.now(timezone.utc)

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
                started_at=now,
                updated_at=now,
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
        task.updated_at = now
        self._session.flush()

        return task

    def mark_completed(
        self,
        task: Task,
        result: dict | None = None,
    ) -> Task:
        """Mark a task as completed."""

        task.mark_completed(result)
        self._session.flush()

        return task

    def mark_failed(
        self,
        task: Task,
        error: dict | None = None,
    ) -> Task:
        """Mark a task as failed."""

        task.mark_failed(error)
        self._session.flush()

        return task

    def increment_retry(
        self,
        task: Task,
    ) -> Task:
        """Increment the task retry counter."""

        task.increment_retry()
        self._session.flush()

        return task