from uuid import uuid4

from database.repositories.approval_repository import (
    ApprovalRepository,
)
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        user = user_repository.create(
            email=f"approval-{uuid4()}@example.com",
            name="Approval Test User",
        )

        repository = ApprovalRepository(session)

        approval = repository.create(
            user_id=user.id,
            action="delete_file",
            reason="Testing human approval workflow.",
            requested_operation="Delete test.py",
            request_payload={
                "path": "test.py",
                "operation": "delete",
            },
        )

        print("CREATED:", approval.id)
        print("STATUS:", approval.status)

        found = repository.get_by_id(approval.id)

        if found is None:
            raise RuntimeError(
                "Approval request could not be read."
            )

        print("READ:", found.action)

        pending = repository.list_pending(
            user_id=user.id
        )

        print(
            "PENDING REQUESTS:",
            len(pending),
        )

        repository.approve(
            found,
            reviewer_id=user.id,
            comment="Approved for testing.",
        )

        print("APPROVED:", found.status)
        print("REVIEWER:", found.reviewed_by)
        print("COMMENT:", found.reviewer_comment)


if __name__ == "__main__":
    main()