"""
Execution service for AI Command Center.

Coordinates task execution through AgentRuntime using an
immutable ExecutionContext.
"""

from __future__ import annotations

import threading
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
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
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

        resolved_execution_id = execution_id or str(task.execution_id or "")
        if not resolved_execution_id:
            resolved_execution_id = f"exec-{task_id}-{threading.get_ident()}"
        resolved_lease_owner_id = lease_owner_id or resolved_execution_id
        if resolved_lease_owner_id != resolved_execution_id:
            return Result.fail(
                "TASK_LEASE_OWNER_MISMATCH",
                "lease_owner_id must match execution_id.",
                details={
                    "task_id": task_id,
                    "execution_id": resolved_execution_id,
                    "lease_owner_id": resolved_lease_owner_id,
                },
            )

        context = ExecutionContext.create(
            user_id=user_id,
            task_id=task_id,
            session_id=session_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            execution_id=resolved_execution_id,
            lease_owner_id=resolved_lease_owner_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=permissions,
            metadata=metadata,
        )

        runtime = runtime_result.require_data()
        heartbeat_stop = threading.Event()
        heartbeat_thread = None

        def _heartbeat_loop() -> None:
            while not heartbeat_stop.wait(30):
                try:
                    self._task_repository.heartbeat(
                        task,
                        resolved_execution_id,
                        lease_owner_id=resolved_lease_owner_id,
                    )
                except Exception:
                    break

        heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            daemon=True,
        )
        heartbeat_thread.start()

        try:
            execution = runtime.execute(
                context=context,
                operation=operation,
            )
        finally:
            heartbeat_stop.set()
            if heartbeat_thread is not None:
                heartbeat_thread.join(timeout=5)

        if execution.result.is_failure():
            return Result.fail(
                execution.result.error.code,
                execution.result.error.message,
                details=execution.result.error.details,
            )

        return Result.ok(execution)