"""
Agent execution endpoints.

Provides the authenticated HTTP boundary for executing a registered
autonomous Agent through the existing AI execution pipeline.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.deps import (
    get_agent_ai_execution_service,
    get_current_user,
    get_db,
)
from api.schemas import (
    AgentExecuteRequest,
    AgentExecuteResponse,
)
from core.pipeline_context import PipelineContext
from database.models.user import User
from services.agent_ai_execution_service import AgentAIExecutionService
from services.agent_runtime_service import AgentRuntimeService
from services.task_service import TaskService


router = APIRouter(
    prefix="/agents",
    tags=["agents"],
)


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build the API's standard error envelope."""

    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }

    if details:
        error["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
        },
    )


def _agent_error_status(code: str) -> int:
    """Map Agent service errors to HTTP status codes."""

    if code == "AGENT_NOT_FOUND":
        return status.HTTP_404_NOT_FOUND

    if code == "AGENT_DISABLED":
        return status.HTTP_409_CONFLICT

    if code == "INVALID_AGENT_ID":
        return status.HTTP_422_UNPROCESSABLE_ENTITY

    return status.HTTP_400_BAD_REQUEST


@router.post(
    "/{agent_id}/execute",
    response_model=AgentExecuteResponse,
)
def execute_agent(
    agent_id: str,
    payload: AgentExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agent_ai_service: AgentAIExecutionService = Depends(
        get_agent_ai_execution_service
    ),
):
    """
    Execute an autonomous Agent request for the authenticated user.

    A persistent Task is created for every valid execution so the
    execution always has the task identity required by ExecutionContext
    and the result can be recovered through the existing task system.
    """

    runtime_service = AgentRuntimeService(db)

    agent_result = runtime_service.get_agent(agent_id)

    if agent_result.is_failure():
        return _error_response(
            status_code=_agent_error_status(
                agent_result.error.code
            ),
            code=agent_result.error.code,
            message=agent_result.error.message,
            details=agent_result.error.details,
        )

    agent = agent_result.require_data()

    task_service = TaskService(db)

    task = task_service.create_task(
        user_id=current_user.id,
        title=f"Agent execution: {agent.name}",
        description=payload.request,
    )

    pipeline_context = PipelineContext(
        task_id=task.id,
        user_id=current_user.id,
        agent_id=agent.id,
    )

    execution_id = pipeline_context.execution_id

    task_service.start_task(
        task.id,
        execution_id=execution_id,
        lease_owner_id=execution_id,
    )

    result = agent_ai_service.execute(
        agent_id=agent.id,
        request=payload.request,
        context=pipeline_context,
    )

    if result.is_failure():
        error_details = dict(
            result.error.details or {}
        )

        error_details.setdefault(
            "task_id",
            task.id,
        )

        error_details.setdefault(
            "execution_id",
            execution_id,
        )

        task_service.fail_task(
            task.id,
            error={
                "code": result.error.code,
                "message": result.error.message,
            },
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        return _error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=result.error.code,
            message=result.error.message,
            details=error_details,
        )

    result_context = result.require_data()

    output = result_context.output_data

    result_payload: dict[str, Any] = {
        "output": output,
        "metadata": dict(result_context.metadata),
        "stage_results": dict(result_context.stage_results),
    }

    task_service.complete_task(
        task.id,
        result_payload,
        execution_id=execution_id,
        lease_owner_id=execution_id,
    )

    return AgentExecuteResponse(
        execution_id=execution_id,
        task_id=task.id,
        agent_id=agent.id,
        status=task.status,
        output=output,
        metadata=dict(result_context.metadata),
    )


__all__ = ["router"]
