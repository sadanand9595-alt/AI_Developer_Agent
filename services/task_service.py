"""
Task service for AI Command Center.

Contains business logic for creating and managing the
lifecycle of AI tasks.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.task import Task
from core.types import TaskStatus
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
        agent_id: str | None = None,
    ) -> Task:
        """Create a new AI task."""

        return self._repository.create(
            user_id=user_id,
            title=title,
            description=description,
            conversation_id=conversation_id,
            priority=priority,
            agent_id=agent_id,
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

    def get_task_by_execution_id(
        self,
        execution_id: str,
    ) -> Task | None:
        """Get a task by execution ID."""

        return self._repository.get_by_execution_id(
            execution_id
        )

    def get_agent_execution(
        self,
        *,
        agent_id: str,
        execution_id: str,
        user_id: str,
    ) -> Task | None:
        """Get an agent execution scoped to the requesting user."""

        task = self._repository.get_by_execution_id_and_user(
            execution_id,
            user_id,
        )

        if task is None:
            return None

        if task.agent_id != agent_id:
            return None

        return task

    def list_agent_executions(
        self,
        *,
        agent_id: str,
        user_id: str,
    ) -> list[Task]:
        """Return agent executions belonging to a user."""

        return self._repository.list_by_agent_and_user(
            agent_id,
            user_id,
        )

    def start_task(
        self,
        task_id: str,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Move a task into the running state."""

        task = self._get_required_task(task_id)

        self._repository.mark_started(
            task,
            execution_id,
            lease_owner_id=lease_owner_id,
        )

        return task

    def complete_task(
        self,
        task_id: str,
        result: dict | None = None,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Mark a task as successfully completed."""

        task = self._get_required_task(task_id)

        self._repository.mark_completed(
            task,
            result,
            execution_id=execution_id,
            lease_owner_id=lease_owner_id,
        )

        return task

    def fail_task(
        self,
        task_id: str,
        error: dict | None = None,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Mark a task as failed."""

        task = self._get_required_task(task_id)

        self._repository.mark_failed(
            task,
            error,
            execution_id=execution_id,
            lease_owner_id=lease_owner_id,
        )

        return task
    def cancel_task(
        self,
        task_id: str,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Mark a running task as cancelled."""

        task = self._get_required_task(task_id)

        self._repository.mark_cancelled(
            task,
            execution_id=execution_id,
            lease_owner_id=lease_owner_id,
        )

        return task

    def pause(
        self,
        task_id: str,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Pause a running task for manual continuation."""

        task = self._get_required_task(task_id)

        self._repository.mark_paused(
            task,
            execution_id=execution_id,
            lease_owner_id=lease_owner_id,
        )

        return task

    def resume_paused(
        self,
        task_id: str,
        *,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
        lease_ttl_seconds: int = 300,
    ) -> Task:
        """Resume a task that was manually paused."""

        task = self._get_required_task(task_id)

        self._repository.resume_paused(
            task,
            execution_id=execution_id,
            lease_owner_id=lease_owner_id,
            lease_ttl_seconds=lease_ttl_seconds,
        )

        return task
    def pause_for_approval(
        self,
        task_id: str,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
    ) -> Task:
        """Pause a running task while waiting for approval."""

        task = self._get_required_task(task_id)

        self._repository.mark_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=lease_owner_id,
        )

        return task

    def resume_waiting_approval(
        self,
        task_id: str,
        *,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
        lease_ttl_seconds: int = 300,
    ) -> Task:
        """Resume a task that is waiting for approval."""

        task = self._get_required_task(task_id)

        self._repository.resume_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=lease_owner_id,
            lease_ttl_seconds=lease_ttl_seconds,
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
    def retry_task(
        self,
        task_id: str,
        *,
        execution_id: str,
        lease_owner_id: str | None = None,
    ) -> Task:
        """
        Retry a failed task.

        The retry receives a new execution identity and is atomically
        transitioned from FAILED to RUNNING.
        """

        task = self._get_required_task(task_id)

        if task.status != TaskStatus.FAILED.value:
            raise ValueError(
                "Only failed tasks can be retried."
            )

        if not isinstance(execution_id, str):
            raise ValueError(
                "execution_id must be a string."
            )

        normalized_execution_id = execution_id.strip()

        if not normalized_execution_id:
            raise ValueError(
                "execution_id cannot be empty."
            )

        normalized_lease_owner_id = (
            lease_owner_id.strip()
            if isinstance(lease_owner_id, str)
            else normalized_execution_id
        )

        if not normalized_lease_owner_id:
            normalized_lease_owner_id = (
                normalized_execution_id
            )

        if (
            normalized_lease_owner_id
            != normalized_execution_id
        ):
            raise ValueError(
                "lease_owner_id must match execution_id."
            )

        return self._repository.retry_failed_task(
            task,
            normalized_execution_id,
            lease_owner_id=normalized_lease_owner_id,
        )

