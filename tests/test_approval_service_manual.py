from uuid import uuid4

from database.session import session_scope
from services.approval_service import ApprovalService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"approval-service-{uuid4()}@example.com",
            name="Approval Service Test User",
        )

        approval_service = ApprovalService(session)

        approval = approval_service.request_approval(
            user_id=user.id,
            action="execute_command",
            reason="Testing human approval workflow.",
            requested_operation="Run test command.",
            request_payload={
                "command": "echo test",
            },
        )

        print("CREATED:", approval.id)
        print("STATUS:", approval.status)
        print("ACTION:", approval.action)

        found = approval_service.get_approval(
            approval.id
        )

        if found is None:
            raise RuntimeError(
                "Approval request could not be retrieved."
            )

        print("READ:", found.action)

        pending = (
            approval_service.get_pending_approvals(
                user.id
            )
        )

        print(
            "PENDING:",
            len(pending),
        )

        approved = approval_service.approve(
            approval.id,
            reviewer_id=user.id,
            comment="Approved for testing.",
        )

        print(
            "APPROVED:",
            approved.status,
        )

        print(
            "REVIEWER:",
            approved.reviewed_by,
        )

        print(
            "COMMENT:",
            approved.reviewer_comment,
        )


if __name__ == "__main__":
    main()