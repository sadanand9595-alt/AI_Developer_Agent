"""
Task lifecycle endpoints.

Every route that operates on an existing task first verifies the
task belongs to the authenticated user (ownership boundary), and
returns 404 -- not 403 -- for a task owned by someone else, so a
caller cannot distinguish "not yours" from "does not exist" (IDOR
prevention).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.pipeline_context import PipelineContext
from services.agent_ai_execution_service import AgentAIExecutionService

from api.deps import (
    get_agent_ai_execution_service,
    get_current_user,
    get_db,
)
from api.schemas import (
    TaskCompleteRequest,
    TaskCreateRequest,
    TaskFailRequest,
    TaskResponse,
)
from database.models.task import Task
from database.models.user import User
from services.task_service import TaskService


router = APIRouter(prefix="/tasks", tags=["tasks"])


def _owned_task(
    task_id: str,
    service: TaskService,
    current_user: User,
) -> Task:
    """Return a task only if it belongs to the current user."""

    task = service.get_task(task_id)

    if task is None or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return task


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    payload: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Create a new task owned by the authenticated user."""

    if payload.conversation_id is not None:
        from services.conversation_service import (
            ConversationService,
        )

        conversation = ConversationService(db).get_conversation(
            payload.conversation_id
        )

        if (
            conversation is None
            or conversation.user_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

    service = TaskService(db)

    return service.create_task(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        conversation_id=payload.conversation_id,
        priority=payload.priority,
    )


@router.get(
    "",
    response_model=list[TaskResponse],
)
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    """List the authenticated user's own tasks."""

    return TaskService(db).list_user_tasks(current_user.id)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Return one of the authenticated user's own tasks."""

    return _owned_task(task_id, TaskService(db), current_user)


@router.post(
    "/{task_id}/start",
    response_model=TaskResponse,
)
def start_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Transition an owned task into the running state."""

    service = TaskService(db)
    _owned_task(task_id, service, current_user)

    return service.start_task(task_id)


@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
)
def complete_task(
    task_id: str,
    payload: TaskCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Mark an owned task as successfully completed."""

    service = TaskService(db)
    _owned_task(task_id, service, current_user)

    return service.complete_task(task_id, payload.result)


@router.post(
    "/{task_id}/fail",
    response_model=TaskResponse,
)
def fail_task(
    task_id: str,
    payload: TaskFailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Mark an owned task as failed."""

    service = TaskService(db)
    _owned_task(task_id, service, current_user)

    return service.fail_task(task_id, payload.error)
@router.post(
    "/{task_id}/retry",
    response_model=TaskResponse,
)
def retry_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agent_ai_service: AgentAIExecutionService = Depends(
        get_agent_ai_execution_service
    ),
) -> Task:
    """
    Retry a failed Agent task.

    The task must belong to the authenticated user and must have
    an associated Agent. A retry receives a new execution ID.
    """

    service = TaskService(db)

    task = _owned_task(
        task_id,
        service,
        current_user,
    )

    if task.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "TASK_NOT_RETRYABLE",
                "message": "Only failed tasks can be retried.",
            },
        )

    if not task.agent_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "TASK_AGENT_REQUIRED",
                "message": "Only Agent execution tasks can be retried.",
            },
        )

    from uuid import uuid4

    execution_id = str(uuid4())

    try:
        task = service.retry_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "TASK_RETRY_FAILED",
                "message": str(exc),
            },
        ) from exc

    pipeline_context = PipelineContext(
        execution_id=execution_id,
        task_id=task.id,
        user_id=current_user.id,
        agent_id=task.agent_id,
    )

    result = agent_ai_service.execute(
        agent_id=task.agent_id,
        request=task.description,
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

        try:
            service.fail_task(
                task.id,
                error={
                    "code": result.error.code,
                    "message": result.error.message,
                },
                execution_id=execution_id,
                lease_owner_id=execution_id,
            )
        except ValueError:
            pass

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": result.error.code,
                "message": result.error.message,
                "details": error_details,
            },
        )

    result_context = result.require_data()

    output = result_context.output_data

    result_payload: dict[str, object] = {
        "output": output,
        "metadata": dict(result_context.metadata),
        "stage_results": dict(
            result_context.stage_results
        ),
    }

    try:
        task = service.complete_task(
            task.id,
            result_payload,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "TASK_COMPLETION_FAILED",
                "message": str(exc),
            },
        ) from exc

    return task