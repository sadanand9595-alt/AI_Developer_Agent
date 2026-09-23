"""
Human approval endpoints.

Ownership model:
- Any authenticated user may view their own approval requests.
- Only an administrator may approve or reject a request (a
  requester approving their own request would defeat the point of
  a human-approval security gate).
- A request belonging to another user is hidden as 404, not
  revealed via 403, for the same non-owner requests (IDOR
  prevention) -- except for administrators, who may act on any
  request as the reviewer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_admin
from api.schemas import ApprovalActionRequest, ApprovalResponse
from database.models.approval import ApprovalRequest
from database.models.user import User
from services.approval_service import ApprovalService
from services.ai_execution_service import AIExecutionService
from services.ai_execution_service import AIExecutionService
from services.task_service import TaskService


router = APIRouter(prefix="/approvals", tags=["approvals"])


def _visible_approval(
    approval_id: str,
    service: ApprovalService,
    current_user: User,
) -> ApprovalRequest:
    """Return an approval visible to the current user (owner or admin)."""

    approval = service.get_approval(approval_id)

    if approval is None or (
        approval.user_id != current_user.id
        and not current_user.is_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )

    return approval


@router.get(
    "/me",
    response_model=list[ApprovalResponse],
)
def list_my_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApprovalRequest]:
    """List the authenticated user's own pending approval requests."""

    return ApprovalService(db).get_pending_approvals(
        user_id=current_user.id
    )


@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
)
def get_approval(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalRequest:
    """Return one approval request (owner or administrator only)."""

    return _visible_approval(
        approval_id,
        ApprovalService(db),
        current_user,
    )


@router.post(
    "/{approval_id}/approve",
    response_model=None,
)
def approve_request(
    approval_id: str,
    payload: ApprovalActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Approve a pending request (administrator only)."""

    service = ApprovalService(db)

    if service.get_approval(approval_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )

    approval = service.approve(
        approval_id,
        reviewer_id=admin.id,
        comment=payload.comment,
    )
    ai_service = getattr(
        request.app.state,
        "ai_execution_service",
        None,
    )
    if approval.execution_id and isinstance(ai_service, AIExecutionService):
        result = ai_service.resume_approved_execution(
            approval.execution_id,
            approval.id,
            approval_service=service,
        )
        return {
            "approval": approval,
            "execution_status": (
                "completed" if result.is_success() else result.error.code
            ),
            "execution_id": approval.execution_id,
            "plan_id": approval.plan_id,
        }
    return approval


@router.post(
    "/{approval_id}/approve",
    response_model=None,
)
def approve_request(
    approval_id: str,
    payload: ApprovalActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Approve a pending request (administrator only)."""

    service = ApprovalService(db)

    if service.get_approval(approval_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )

    approval = service.approve(
        approval_id,
        reviewer_id=admin.id,
        comment=payload.comment,
    )

    ai_service = getattr(
        request.app.state,
        "ai_execution_service",
        None,
    )

    if approval.execution_id and isinstance(
        ai_service,
        AIExecutionService,
    ):
        task_service = TaskService(db)

        result = ai_service.resume_approved_execution(
            approval.execution_id,
            approval.id,
            approval_service=service,
            task_service=task_service,
        )

        return {
            "approval": approval,
            "execution_status": (
                "completed"
                if result.is_success()
                else result.error.code
            ),
            "execution_id": approval.execution_id,
            "plan_id": approval.plan_id,
        }

    return approval