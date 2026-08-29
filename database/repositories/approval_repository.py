"""
Approval repository for AI Command Center.

Provides persistence operations for human approval requests.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.types import ApprovalStatus
from database.models.approval import ApprovalRequest


class ApprovalRepository:
    """Persistence operations for approval requests."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: str,
        action: str,
        reason: str,
        requested_operation: str,
        task_id: str | None = None,
        tool_id: str | None = None,
        request_payload: dict | None = None,
        expires_at=None,
    ) -> ApprovalRequest:
        """Create a pending approval request."""

        if not action.strip():
            raise ValueError(
                "Approval action cannot be empty."
            )

        if not reason.strip():
            raise ValueError(
                "Approval reason cannot be empty."
            )

        if not requested_operation.strip():
            raise ValueError(
                "Requested operation cannot be empty."
            )

        approval = ApprovalRequest(
            user_id=user_id,
            task_id=task_id,
            tool_id=tool_id,
            action=action.strip(),
            reason=reason.strip(),
            requested_operation=requested_operation.strip(),
            request_payload=request_payload,
            status=ApprovalStatus.PENDING.value,
            expires_at=expires_at,
        )

        self._session.add(approval)
        self._session.flush()

        return approval

    def get_by_id(
        self,
        approval_id: str,
    ) -> ApprovalRequest | None:
        """Return an approval request by ID."""

        statement = select(ApprovalRequest).where(
            ApprovalRequest.id == approval_id
        )

        return self._session.scalar(statement)

    def list_pending(
        self,
        user_id: str | None = None,
    ) -> list[ApprovalRequest]:
        """Return pending approval requests."""

        statement = select(ApprovalRequest).where(
            ApprovalRequest.status
            == ApprovalStatus.PENDING.value
        )

        if user_id is not None:
            statement = statement.where(
                ApprovalRequest.user_id == user_id
            )

        statement = statement.order_by(
            ApprovalRequest.requested_at.asc()
        )

        return list(
            self._session.scalars(statement).all()
        )

    def approve(
        self,
        approval: ApprovalRequest,
        reviewer_id: str,
        comment: str | None = None,
    ) -> ApprovalRequest:
        """Approve a pending request."""

        approval.approve(
            reviewer_id=reviewer_id,
            comment=comment,
        )

        self._session.flush()

        return approval

    def reject(
        self,
        approval: ApprovalRequest,
        reviewer_id: str,
        comment: str | None = None,
    ) -> ApprovalRequest:
        """Reject a pending request."""

        approval.reject(
            reviewer_id=reviewer_id,
            comment=comment,
        )

        self._session.flush()

        return approval

    def expire(
        self,
        approval: ApprovalRequest,
    ) -> ApprovalRequest:
        """Expire a pending request."""

        approval.expire()

        self._session.flush()

        return approval