from datetime import datetime, timedelta, timezone
from uuid import uuid4

from database.models.approval import ApprovalRequest
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
            password_hash="test-hash-not-used",
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

    # -------------------------------------------------
    # EXPIRED APPROVAL SECURITY BOUNDARY
    # -------------------------------------------------
    #
    # A pending request whose expires_at has already passed
    # must not be approvable. Approving it would authorize a
    # gated action after the human-approval window has closed.
    # -------------------------------------------------

    expired = ApprovalRequest(
        id="expired-approval-1",
        user_id="user-1",
        action="delete_file",
        reason="Testing expiration boundary.",
        requested_operation="Delete test.py",
        status="pending",
        expires_at=(
            datetime.now(timezone.utc)
            - timedelta(hours=1)
        ),
    )

    try:
        expired.approve(reviewer_id="reviewer-1")
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "Expired approval request should be rejected."
        )

    if expired.status != "expired":
        raise RuntimeError(
            "Expired approval attempt should transition "
            f"status to expired, got: {expired.status}"
        )

    print("EXPIRED APPROVAL PROTECTION: PASS")

    # -------------------------------------------------
    # CONCURRENT DOUBLE-APPROVAL PROTECTION
    # -------------------------------------------------
    #
    # Two sessions each load the same PENDING approval before
    # either writes. The first to persist must win; the second
    # -- which is now acting on a stale in-memory copy -- must be
    # rejected instead of silently overwriting the first reviewer's
    # decision while still reporting success.
    # -------------------------------------------------

    with session_scope() as setup_session:
        setup_user = UserRepository(setup_session).create(
            email=f"race-user-{uuid4()}@example.com",
            name="Race Test User",
            password_hash="test-hash-not-used",
        )

        race_approval = ApprovalRepository(setup_session).create(
            user_id=setup_user.id,
            action="delete_file",
            reason="Testing concurrent approval protection.",
            requested_operation="Delete test.py",
        )
        race_approval_id = race_approval.id
        race_user_id = setup_user.id

    with session_scope() as session_a:
        approval_a = ApprovalRepository(
            session_a
        ).get_by_id(race_approval_id)

        with session_scope() as session_b:
            approval_b = ApprovalRepository(
                session_b
            ).get_by_id(race_approval_id)

            # session_b commits first, simulating the winner of
            # a real concurrent race.
            ApprovalRepository(session_b).approve(
                approval_b,
                reviewer_id=race_user_id,
                comment="First reviewer wins.",
            )

        # session_a is still holding the pre-approval snapshot it
        # loaded before session_b committed.
        try:
            ApprovalRepository(session_a).approve(
                approval_a,
                reviewer_id=race_user_id,
                comment="Second reviewer should be rejected.",
            )
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Stale concurrent approve() should be rejected."
            )

    with session_scope() as verify_session:
        final = ApprovalRepository(verify_session).get_by_id(
            race_approval_id
        )

        if final.reviewer_comment != "First reviewer wins.":
            raise RuntimeError(
                "The first, winning approval was overwritten by "
                "the stale concurrent one."
            )

    print("CONCURRENT DOUBLE-APPROVAL PROTECTION: PASS")


if __name__ == "__main__":
    main()