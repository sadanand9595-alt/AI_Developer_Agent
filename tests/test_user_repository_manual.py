from uuid import uuid4

from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    email = f"test-{uuid4()}@example.com"

    with session_scope() as session:
        repository = UserRepository(session)

        user = repository.create(
            email=email,
            name="Test User",
        )

        user_id = user.id

        print("CREATED:", user.id, user.email)

        found = repository.get_by_id(user_id)

        if found is None:
            raise RuntimeError("User could not be read.")

        print("READ:", found.name)

        repository.update_name(
            found,
            "Updated Test User",
        )

        print("UPDATED:", found.name)

        repository.deactivate(found)

        print("DEACTIVATED:", found.is_active)


if __name__ == "__main__":
    main()