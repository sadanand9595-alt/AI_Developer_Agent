from uuid import uuid4

from database.session import session_scope
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        service = UserService(session)

        email = f"service-{uuid4()}@example.com"

        user = service.create_user(
            email=email,
            name="Service Test User",
        )

        print("CREATED:", user.id, user.email)
        print("ACTIVE:", user.is_active)

        found = service.get_user(user.id)

        if found is None:
            raise RuntimeError(
                "User could not be retrieved."
            )

        print("READ:", found.name)

        updated = service.update_name(
            user.id,
            "Updated Service User",
        )

        print("UPDATED:", updated.name)

        same_user = service.get_user_by_email(
            email
        )

        if same_user is None:
            raise RuntimeError(
                "User could not be found by email."
            )

        print("EMAIL LOOKUP:", same_user.email)

        deactivated = service.deactivate_user(
            user.id
        )

        print(
            "DEACTIVATED:",
            deactivated.is_active,
        )

        active_users = service.list_active_users()

        print(
            "ACTIVE USERS:",
            len(active_users),
        )


if __name__ == "__main__":
    main()