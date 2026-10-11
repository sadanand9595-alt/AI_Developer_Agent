"""
Sequential multi-agent orchestration endpoints.

Provides the HTTP boundary for Phase 8.1 sequential
specialist orchestration under one durable parent Task.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import (
    get_agent_ai_execution_service,
    get_current_user,
    get_db,
)
from api.schemas import (
    OrchestrationSpecialistRequest,
    SequentialOrchestrationRequest,
    SequentialOrchestrationResponse,
)
from database.models.user import User
from services.agent_ai_execution_service import AgentAIExecutionService
from services.agent_orchestration_service import (
    AgentOrchestrationService,
    SpecialistSpec,
)


router = APIRouter(
    prefix="/orchestrations",
    tags=["orchestrations"],
)


@router.post(
    "/sequential",
    response_model=SequentialOrchestrationResponse,
)
def execute_sequential_orchestration(
    payload: SequentialOrchestrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agent_ai_service: AgentAIExecutionService = Depends(
        get_agent_ai_execution_service
    ),
) -> SequentialOrchestrationResponse:
    """Execute a sequential specialist orchestration."""

    specialists = [
        SpecialistSpec(
            agent_id=specialist.agent_id,
            name=specialist.name,
        )
        for specialist in payload.specialists
    ]

    service = AgentOrchestrationService(
        session=db,
        agent_ai_service=agent_ai_service,
    )

    result = service.execute_sequential(
        user_id=current_user.id,
        request=payload.request,
        specialists=specialists,
        title=payload.title,
    )

    if result.is_failure():
        error = result.error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": (
                    error.code
                    if error is not None
                    else "ORCHESTRATION_FAILED"
                ),
                "message": (
                    error.message
                    if error is not None
                    else "Orchestration failed."
                ),
                "details": (
                    dict(error.details)
                    if error is not None
                    else {}
                ),
            },
        )

    data: dict[str, Any] = result.require_data()

    return SequentialOrchestrationResponse(
        task_id=data["task_id"],
        execution_id=data["execution_id"],
        status=data["status"],
        partial_result=data["partial_result"],
        successful_count=data["successful_count"],
        failed_count=data["failed_count"],
        specialists=data["specialists"],
        final_output=data.get("final_output"),
        error=data.get("error"),
    )
