"""
Task service for AI Command Center.

Contains business logic for creating and managing the
lifecycle of AI tasks.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.task import Task
from database.repositories.task_repository import TaskRepository


class TaskService:
    """Business operations for AI tasks."""

    def __init__(self, session: Session) -> None:
        self._repository = TaskRepository(session)

    def create_task(
        self,
        *,
        user_id: str,
        title: str,
        description: str,
        conversation_id: str | None = None,
        priority: int = 0,
    ) -> Task:
        """Create a new AI task."""

        return self._repository.create(
            user_id=user_id,
            title=title,
            description=description,
            conversation_id=conversation_id,
            priority=priority,
        )

    def get_task(
        self,
        task_id: str,
    ) -> Task | None:
        """Get a task by ID."""

        return self._repository.get_by_id(task_id)

    def list_user_tasks(
        self,
        user_id: str,
    ) -> list[Task]:
        """Return all tasks belonging to a user."""

        return self._repository.list_by_user(user_id)

    def list_pending_tasks(self) -> list[Task]:
        """Return tasks waiting for execution."""

        return self._repository.list_pending()

    def start_task(
        self,
        task_id: str,
        execution_id: str | None = None,
    ) -> Task:
        """Move a task into the running state."""

        task = self._get_required_task(task_id)

        self._repository.mark_started(
            task,
            execution_id,
        )

        return task

    def complete_task(
        self,
        task_id: str,
        result: dict | None = None,
    ) -> Task:
        """Mark a task as successfully completed."""

        task = self._get_required_task(task_id)

        self._repository.mark_completed(
            task,
            result,
        )

        return task

    def fail_task(
        self,
        task_id: str,
        error: dict | None = None,
    ) -> Task:
        """Mark a task as failed."""

        task = self._get_required_task(task_id)

        self._repository.mark_failed(
            task,
            error,
        )

        return task

    def retry_task(
        self,
        task_id: str,
    ) -> Task:
        """Increment retry count for a failed task."""

        task = self._get_required_task(task_id)

        self._repository.increment_retry(task)

        return task

    def _get_required_task(
        self,
        task_id: str,
    ) -> Task:
        """Return a task or raise a controlled error."""

        task = self._repository.get_by_id(task_id)

        if task is None:
            raise ValueError("Task not found.")

        return task