"""
Execution observability and cancellation endpoints.

Provides authenticated, user-scoped access to live execution
progress, observation snapshots, audit records, and cancellation.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from database.models.user import User
from database.repositories.task_repository import TaskRepository
from services.ai_execution_service import AIExecutionService
from services.task_service import TaskService


router = APIRouter(
    prefix="/executions",
    tags=["executions"],
)


def _get_ai_execution_service(
    request: Request,
) -> AIExecutionService:
    """Return the application-scoped AI execution service."""

    service = getattr(
        request.app.state,
        "ai_execution_service",
        None,
    )

    if not isinstance(service, AIExecutionService):
        raise RuntimeError(
            "AI execution service is not initialized."
        )

    return service


def _get_owned_task(
    *,
    execution_id: str,
    current_user: User,
    db: Session,
):
    """
    Resolve an execution to a durable Task owned by the current user.

    The durable Task is the authorization boundary. Runtime
    observability and cancellation are never exposed before
    ownership is verified.
    """

    normalized_execution_id = execution_id.strip()

    if not normalized_execution_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )

    task = TaskRepository(db).get_by_execution_id_and_user(
        normalized_execution_id,
        current_user.id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )

    return task


@router.get(
    "/{execution_id}/progress",
)
def get_execution_progress(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AIExecutionService = Depends(
        _get_ai_execution_service
    ),
) -> dict[str, Any]:
    """Return live progress for an execution owned by the current user."""

    task = _get_owned_task(
        execution_id=execution_id,
        current_user=current_user,
        db=db,
    )

    runtime_execution_id = task.execution_id or execution_id

    progress = service._execution_system.get_progress(
        runtime_execution_id
    )

    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live execution progress not found.",
        )

    return {
        "execution_id": progress.execution_id,
        "task_id": task.id,
        "total_steps": progress.total_steps,
        "completed_steps": progress.completed_steps,
        "current_step": progress.current_step,
        "status": progress.status,
        "started_at": progress.started_at,
        "updated_at": progress.updated_at,
        "progress_percent": progress.progress_percent,
    }


@router.get(
    "/{execution_id}/observation",
)
def get_execution_observation(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AIExecutionService = Depends(
        _get_ai_execution_service
    ),
) -> dict[str, Any]:
    """Return live observation for an execution owned by the current user."""

    task = _get_owned_task(
        execution_id=execution_id,
        current_user=current_user,
        db=db,
    )

    runtime_execution_id = task.execution_id or execution_id

    observation = service._execution_system.get_observation(
        runtime_execution_id
    )

    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live execution observation not found.",
        )

    payload = asdict(observation)

    payload["task_id"] = task.id

    if observation.total_steps > 0:
        payload["progress_percent"] = (
            observation.completed_steps
            / observation.total_steps
        ) * 100.0
    else:
        payload["progress_percent"] = 0.0

    return payload


@router.get(
    "/{execution_id}/audit",
)
def get_execution_audit(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AIExecutionService = Depends(
        _get_ai_execution_service
    ),
) -> dict[str, Any]:
    """Return audit records for an execution owned by the current user."""

    task = _get_owned_task(
        execution_id=execution_id,
        current_user=current_user,
        db=db,
    )

    runtime_execution_id = task.execution_id or execution_id

    records = service._execution_system.get_audit(
        runtime_execution_id
    )

    return {
        "execution_id": runtime_execution_id,
        "task_id": task.id,
        "count": len(records),
        "events": [
            asdict(record)
            for record in records
        ],
    }


@router.post(
    "/{execution_id}/cancel",
)
def cancel_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AIExecutionService = Depends(
        _get_ai_execution_service
    ),
) -> dict[str, Any]:
    """
    Cancel an execution owned by the current user.

    Cancellation updates both the live execution runtime
    and the durable Task record.
    """

    task = _get_owned_task(
        execution_id=execution_id,
        current_user=current_user,
        db=db,
    )

    runtime_execution_id = task.execution_id or execution_id

    # Preserve the lease owner before runtime cancellation changes
    # the durable task state.
    lease_owner_id = task.lease_owner_id

    result = service.cancel_execution(
        runtime_execution_id,
    )

    if result.error is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution cancellation returned an invalid result.",
        )

    if result.error.code == "EXECUTION_CANCELLED":
        try:
            TaskService(db).cancel_task(
                task.id,
                execution_id=runtime_execution_id,
                lease_owner_id=lease_owner_id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "TASK_CANCELLATION_FAILED",
                    "message": str(exc),
                },
            ) from exc

        return {
            "execution_id": runtime_execution_id,
            "task_id": task.id,
            "status": "cancelled",
            "message": "Execution cancelled successfully.",
        }

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": result.error.code,
            "message": result.error.message,
        },
    )


__all__ = ["router"]