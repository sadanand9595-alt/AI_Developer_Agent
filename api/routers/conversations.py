"""
Conversation and message endpoints.

Ownership is enforced the same way as tasks.py: a conversation
belonging to another user returns 404, never 403, to avoid leaking
its existence (IDOR prevention).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import (
    get_ai_execution_service,
    get_current_user,
    get_db,
)
from api.schemas import (
    ConversationCreateRequest,
    ConversationResponse,
    AIMessageResponse,
    MessageCreateRequest,
    MessageResponse,
)
from database.models.conversation import Conversation
from database.models.user import User
from core.pipeline_context import PipelineContext
from services.conversation_service import ConversationService
from services.message_service import MessageService
from services.ai_execution_service import AIExecutionService
from services.approval_service import ApprovalService


router = APIRouter(prefix="/conversations", tags=["conversations"])


def _owned_conversation(
    conversation_id: str,
    service: ConversationService,
    current_user: User,
) -> Conversation:
    """Return a conversation only if it belongs to the current user."""

    conversation = service.get_conversation(conversation_id)

    if (
        conversation is None
        or conversation.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Conversation:
    """Create a new conversation owned by the authenticated user."""

    return ConversationService(db).create_conversation(
        user_id=current_user.id,
        title=payload.title,
        system_context=payload.system_context,
    )


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def list_conversations(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Conversation]:
    """List the authenticated user's own conversations."""

    return ConversationService(db).list_user_conversations(
        current_user.id,
        include_archived=include_archived,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Conversation:
    """Return one of the authenticated user's own conversations."""

    return _owned_conversation(
        conversation_id,
        ConversationService(db),
        current_user,
    )


@router.post(
    "/{conversation_id}/archive",
    response_model=ConversationResponse,
)
def archive_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Conversation:
    """Archive an owned conversation."""

    service = ConversationService(db)
    _owned_conversation(conversation_id, service, current_user)

    return service.archive_conversation(conversation_id)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a user message to an owned conversation.

    Rejects a nonexistent or archived conversation via the existing,
    already-audited MessageService parent-lifecycle checks.
    """

    _owned_conversation(
        conversation_id,
        ConversationService(db),
        current_user,
    )

    return MessageService(db).add_user_message(
        conversation_id=conversation_id,
        content=payload.content,
        metadata=payload.metadata,
    )


@router.post(
    "/{conversation_id}/messages/execute",
    response_model=AIMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIExecutionService = Depends(get_ai_execution_service),
) -> AIMessageResponse:
    """Persist a user message, execute it, and persist the assistant result."""

    _owned_conversation(
        conversation_id,
        ConversationService(db),
        current_user,
    )

    message_service = MessageService(db)
    user_message = message_service.add_user_message(
        conversation_id=conversation_id,
        content=payload.content,
        metadata=payload.metadata,
    )
    db.commit()

    context_result = ai_service.execute(
        payload.content,
        approval_service=ApprovalService(db),
        context=PipelineContext(
            user_id=current_user.id,
            metadata={"conversation_id": conversation_id},
        ),
    )

    if context_result.is_failure():
        if context_result.error.code == "APPROVAL_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "code": context_result.error.code,
                    "message": context_result.error.message,
                    **context_result.error.details,
                },
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": context_result.error.code,
                "message": context_result.error.message,
            },
        )

    context = context_result.require_data()
    assistant_message = message_service.add_assistant_message(
        conversation_id=conversation_id,
        content=str(context.output_data),
        metadata={
            "execution_id": context.execution_id,
            "stage_results": context.stage_results,
        },
    )

    return AIMessageResponse(
        user_message=user_message,
        assistant_message=assistant_message,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def list_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List messages in an owned conversation, chronologically."""

    _owned_conversation(
        conversation_id,
        ConversationService(db),
        current_user,
    )

    return MessageService(db).get_conversation_messages(
        conversation_id
    )
