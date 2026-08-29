"""
Execution orchestrator for AI Command Center.

Coordinates task state, agent runtime execution, and
execution result persistence.
"""

from __future__ import annotations

from typing import Callable, TypeVar

from sqlalchemy.orm import Session

from core.context import ExecutionContext
from core.result import Result
from database.repositories.task_repository import TaskRepository
from services.agent_runtime_service import AgentRuntimeService
from services.execution_service import ExecutionService
from services.execution_state_service import ExecutionStateService
from services.task_service import TaskService


T = TypeVar("T")


class ExecutionOrchestrator:
    """Coordinate the complete controlled execution workflow."""

    def __init__(
        self,
        session: Session,
        agent_runtime_service: AgentRuntimeService | None = None,
    ) -> None:
        self._task_service = TaskService(session)

        self._task_repository = TaskRepository(
            session
        )

        self._agent_runtime_service = (
            agent_runtime_service
            if agent_runtime_service is not None
            else AgentRuntimeService(session)
        )

        self._execution_service = ExecutionService(
            session,
            agent_runtime_service=(
                self._agent_runtime_service
            ),
        )

        self._state_service = ExecutionStateService(
            self._task_repository
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
    ) -> Result[T]:
        """Execute a task through the complete orchestration flow."""

        task = self._task_service.get_task(
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

        if task.user_id != user_id:
            return Result.fail(
                "TASK_ACCESS_DENIED",
                "Task does not belong to the supplied user.",
                details={
                    "task_id": task_id,
                    "user_id": user_id,
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

        started = self._state_service.mark_started(
            task
        )

        if started.is_failure():
            return Result.fail(
                started.error.code,
                started.error.message,
                details=started.error.details,
            )

        execution_result = self._execution_service.execute(
            task_id=task_id,
            user_id=user_id,
            agent_id=agent_id,
            operation=operation,
            session_id=session_id,
            conversation_id=conversation_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=permissions,
            metadata=metadata,
        )

        if execution_result.is_failure():
            self._state_service.mark_failure(
                task,
                {
                    "code": execution_result.error.code,
                    "message": execution_result.error.message,
                },
            )

            return Result.fail(
                execution_result.error.code,
                execution_result.error.message,
                details=execution_result.error.details,
            )

        execution = execution_result.require_data()

        if execution.result.is_failure():
            self._state_service.mark_failure(
                task,
                {
                    "code": execution.result.error.code,
                    "message": execution.result.error.message,
                },
            )

            return Result.fail(
                execution.result.error.code,
                execution.result.error.message,
                details=execution.result.error.details,
            )

        completed = self._state_service.mark_success(
            task,
            execution.result.data
            if isinstance(
                execution.result.data,
                dict,
            )
            else {
                "result": execution.result.data,
            },
        )

        if completed.is_failure():
            return Result.fail(
                completed.error.code,
                completed.error.message,
                details=completed.error.details,
            )

        return Result.ok(
            execution.result.data
        )