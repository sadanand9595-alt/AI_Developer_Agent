"""
Execution service for AI Command Center.

Coordinates task execution through AgentRuntime using an
immutable ExecutionContext.
"""

from __future__ import annotations

from typing import Callable, TypeVar

from sqlalchemy.orm import Session

from core.agent_runtime import AgentExecution
from core.context import ExecutionContext
from core.result import Result
from database.repositories.task_repository import TaskRepository
from services.agent_runtime_service import AgentRuntimeService


T = TypeVar("T")


class ExecutionService:
    """Coordinate controlled task execution."""

    def __init__(
        self,
        session: Session,
        agent_runtime_service: AgentRuntimeService | None = None,
    ) -> None:
        self._task_repository = TaskRepository(session)
        self._agent_runtime_service = (
            agent_runtime_service
            if agent_runtime_service is not None
            else AgentRuntimeService(session)
        )

    def execute(
        self,
        *,
        task_id: str,
        user_id: str,
        agent_id: str,
        operation: Callable[
            [ExecutionContext],
            Result[T],
        ],
        session_id: str | None = None,
        conversation_id: str | None = None,
        workspace_root: str = ".",
        working_directory: str = ".",
        permissions: set[str] | frozenset[str] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Result[AgentExecution[T]]:
        """
        Execute a task through the selected agent runtime.
        """

        task = self._task_repository.get_by_id(
            task_id
        )

        if task is None:
            return Result.fail(
                "TASK_NOT_FOUND",
                "Task was not found.",
                details={
                    "task_id": task_id,
                },
            )

        runtime_result = (
            self._agent_runtime_service.get_runtime(
                agent_id
            )
        )

        if runtime_result.is_failure():
            return Result.fail(
                runtime_result.error.code,
                runtime_result.error.message,
                details=runtime_result.error.details,
            )

        context = ExecutionContext.create(
            user_id=user_id,
            task_id=task_id,
            session_id=session_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=permissions,
            metadata=metadata,
        )

        runtime = runtime_result.require_data()

        execution = runtime.execute(
            context=context,
            operation=operation,
        )

        if execution.result.is_failure():
            return Result.fail(
                execution.result.error.code,
                execution.result.error.message,
                details=execution.result.error.details,
            )

        return Result.ok(execution)