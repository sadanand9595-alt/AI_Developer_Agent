from uuid import uuid4

from database.repositories.audit_repository import AuditRepository
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        user = user_repository.create(
            email=f"audit-{uuid4()}@example.com",
            name="Audit Test User",
        )

        repository = AuditRepository(session)

        audit = repository.create(
            user_id=user.id,
            action="test_execution",
            category="testing",
            status="success",
            message="Audit repository test completed.",
            metadata={
                "environment": "development",
                "test": True,
            },
        )

        print("CREATED:", audit.id)
        print("ACTION:", audit.action)
        print("STATUS:", audit.status)

        found = repository.get_by_id(audit.id)

        if found is None:
            raise RuntimeError(
                "Audit record could not be read."
            )

        print("READ:", found.action)

        records = repository.list_by_user(
            user.id
        )

        print(
            "USER AUDIT RECORDS:",
            len(records),
        )

        action_records = repository.list_by_action(
            "test_execution"
        )

        print(
            "ACTION RECORDS:",
            len(action_records),
        )

        print(
            "METADATA:",
            found.metadata_json,
        )


if __name__ == "__main__":
    main()