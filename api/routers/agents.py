"""
Agent management and execution endpoints.

Provides the authenticated HTTP boundary for managing registered
system-wide Agents and executing them through the existing autonomous
AI execution pipeline.
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
    AgentCreateRequest,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentResponse,
    AgentUpdateRequest,
)
from core.pipeline_context import PipelineContext
from database.models.agent import Agent
from database.models.user import User
from services.agent_ai_execution_service import AgentAIExecutionService
from services.agent_runtime_service import AgentRuntimeService
from services.agent_service import AgentService
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


# ---------------------------------------------------------------------------
# Agent Management
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent(
    payload: AgentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """
    Create a new system-wide Agent.

    Agents are currently system-wide resources and are therefore
    not owned by the authenticated user.
    """

    service = AgentService(db)

    agent = service.register_agent(
        name=payload.name,
        agent_type=payload.agent_type,
        description=payload.description,
        model_provider=payload.model_provider,
        model_name=payload.model_name,
        capabilities=payload.capabilities,
        configuration=payload.configuration,
        max_iterations=payload.max_iterations,
    )

    return agent


@router.get(
    "",
    response_model=list[AgentResponse],
)
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Agent]:
    """List all registered system-wide Agents."""

    return AgentService(db).list_agents()


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
)
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """Return one registered Agent."""

    agent = AgentService(db).get_agent(agent_id)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    return agent


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
)
def update_agent(
    agent_id: str,
    payload: AgentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """Update an Agent's editable configuration."""

    if not payload.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field is required.",
        )

    service = AgentService(db)

    values = payload.model_dump(
        exclude_unset=True,
    )

    agent = service.update_agent(
        agent_id,
        name=values.get("name"),
        agent_type=values.get("agent_type"),
        description=values.get("description"),
        model_provider=values.get("model_provider"),
        model_name=values.get("model_name"),
        capabilities=values.get("capabilities"),
        configuration=values.get("configuration"),
        max_iterations=values.get("max_iterations"),
        update_description="description" in values,
        update_model_provider="model_provider" in values,
        update_model_name="model_name" in values,
        update_capabilities="capabilities" in values,
        update_configuration="configuration" in values,
    )

    return agent


@router.post(
    "/{agent_id}/enable",
    response_model=AgentResponse,
)
def enable_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """Enable an Agent."""

    return AgentService(db).activate_agent(agent_id)


@router.post(
    "/{agent_id}/disable",
    response_model=AgentResponse,
)
def disable_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """Disable an Agent."""

    return AgentService(db).disable_agent(agent_id)


# ---------------------------------------------------------------------------
# Agent Execution
# ---------------------------------------------------------------------------


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