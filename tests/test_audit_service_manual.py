from uuid import uuid4

from database.session import session_scope
from services.audit_service import AuditService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"audit-service-{uuid4()}@example.com",
            name="Audit Service Test User",
            password_hash="test-hash-not-used",
        )

        audit_service = AuditService(session)

        event = audit_service.record_event(
            user_id=user.id,
            action="test_execution",
            category="testing",
            status="success",
            message="AuditService test completed.",
            metadata={
                "environment": "development",
                "test": True,
            },
        )

        print("CREATED:", event.id)
        print("ACTION:", event.action)
        print("STATUS:", event.status)

        found = audit_service.get_event(
            event.id
        )

        if found is None:
            raise RuntimeError(
                "Audit event could not be retrieved."
            )

        print("READ:", found.action)

        user_events = audit_service.get_user_events(
            user.id
        )

        print(
            "USER EVENTS:",
            len(user_events),
        )

        action_events = audit_service.get_action_events(
            "test_execution"
        )

        print(
            "ACTION EVENTS:",
            len(action_events),
        )

        print(
            "MESSAGE:",
            found.message,
        )

        print(
            "METADATA:",
            found.metadata_json,
        )


if __name__ == "__main__":
    main()