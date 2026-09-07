"""
Approval repository for AI Command Center.

Provides persistence operations for human approval requests.
"""

from __future__ import annotations

from sqlalchemy import select, update
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
        execution_id: str | None = None,
        plan_id: str | None = None,
        step_id: str | None = None,
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
            execution_id=execution_id,
            plan_id=plan_id,
            step_id=step_id,
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

        previous_status = approval.status

        approval.approve(
            reviewer_id=reviewer_id,
            comment=comment,
        )

        self._commit_transition(approval, previous_status)

        return approval

    def reject(
        self,
        approval: ApprovalRequest,
        reviewer_id: str,
        comment: str | None = None,
    ) -> ApprovalRequest:
        """Reject a pending request."""

        previous_status = approval.status

        approval.reject(
            reviewer_id=reviewer_id,
            comment=comment,
        )

        self._commit_transition(approval, previous_status)

        return approval

    def _commit_transition(
        self,
        approval: ApprovalRequest,
        previous_status: str,
    ) -> None:
        """
        Persist a status transition atomically.

        approval.approve()/reject() already validated and mutated
        the in-memory object above. Two concurrent requests can
        both load the same PENDING row, both pass that in-memory
        validation, and both attempt to persist -- a plain flush()
        has no way to detect this and would let both "succeed"
        (whichever commits last silently overwrites the other,
        while both callers are told 200 OK). This closes that
        window with a single atomic UPDATE conditioned on the
        status the row was actually in when we started, so a
        second, now-stale writer gets 0 affected rows instead of a
        silent overwrite.
        """

        with self._session.no_autoflush:
            result = self._session.execute(
                update(ApprovalRequest)
                .where(
                    ApprovalRequest.id == approval.id,
                    ApprovalRequest.status == previous_status,
                )
                .values(
                    status=approval.status,
                    reviewed_by=approval.reviewed_by,
                    reviewer_comment=approval.reviewer_comment,
                    reviewed_at=approval.reviewed_at,
                )
            )

        if result.rowcount == 0:
            self._session.expire(approval)

            raise ValueError(
                "Approval request was already updated by a "
                "concurrent request."
            )

        # The row was written via a Core statement, bypassing the
        # ORM unit-of-work. Refresh so the in-memory object matches
        # what was persisted and is no longer considered dirty
        # (otherwise a later flush could re-issue a redundant,
        # unconditioned UPDATE for the same object).
        self._session.refresh(approval)

    def expire(
        self,
        approval: ApprovalRequest,
    ) -> ApprovalRequest:
        """Expire a pending request."""

        approval.expire()

        self._session.flush()

        return approval