"""
Approval service for AI Command Center.

Contains business logic for human approval workflows.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.approval import ApprovalRequest
from database.repositories.approval_repository import ApprovalRepository


class ApprovalService:
    """Business operations for approval requests."""

    def __init__(self, session: Session) -> None:
        self._repository = ApprovalRepository(session)

    def request_approval(
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
        """Create a new human approval request."""

        return self._repository.create(
            user_id=user_id,
            action=action,
            reason=reason,
            requested_operation=requested_operation,
            task_id=task_id,
            tool_id=tool_id,
            request_payload=request_payload,
            expires_at=expires_at,
        )

    def get_approval(
        self,
        approval_id: str,
    ) -> ApprovalRequest | None:
        """Get an approval request by ID."""

        return self._repository.get_by_id(approval_id)

    def get_pending_approvals(
        self,
        user_id: str | None = None,
    ) -> list[ApprovalRequest]:
        """Return pending approval requests."""

        return self._repository.list_pending(
            user_id=user_id
        )

    def approve(
        self,
        approval_id: str,
        reviewer_id: str,
        comment: str | None = None,
    ) -> ApprovalRequest:
        """Approve a pending request."""

        approval = self._get_required_approval(
            approval_id
        )

        return self._repository.approve(
            approval,
            reviewer_id=reviewer_id,
            comment=comment,
        )

    def reject(
        self,
        approval_id: str,
        reviewer_id: str,
        comment: str | None = None,
    ) -> ApprovalRequest:
        """Reject a pending request."""

        approval = self._get_required_approval(
            approval_id
        )

        return self._repository.reject(
            approval,
            reviewer_id=reviewer_id,
            comment=comment,
        )

    def expire(
        self,
        approval_id: str,
    ) -> ApprovalRequest:
        """Expire a pending request."""

        approval = self._get_required_approval(
            approval_id
        )

        return self._repository.expire(approval)

    def _get_required_approval(
        self,
        approval_id: str,
    ) -> ApprovalRequest:
        """Return an approval or raise a controlled error."""

        approval = self._repository.get_by_id(
            approval_id
        )

        if approval is None:
            raise ValueError(
                "Approval request not found."
            )

        return approval