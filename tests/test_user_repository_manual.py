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
            password_hash="test-hash-not-used",
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

        # -------------------------------------------------
        # NON-STRING FIELD SAFETY
        # -------------------------------------------------
        #
        # create()/get_by_email()/update_name() called .strip()
        # before checking isinstance(x, str), crashing with an
        # unrelated AttributeError for non-string input instead
        # of a clean ValueError/None.
        # -------------------------------------------------

        for bad_kwargs in (
            {"email": None, "name": "x", "password_hash": "h"},
            {"email": 123, "name": "x", "password_hash": "h"},
            {"email": "a@b.com", "name": None, "password_hash": "h"},
        ):
            try:
                repository.create(**bad_kwargs)
            except ValueError:
                pass
            else:
                raise RuntimeError(
                    f"Non-string field {bad_kwargs!r} should "
                    "be rejected."
                )

        if repository.get_by_email(None) is not None:
            raise RuntimeError(
                "Non-string email lookup should return None."
            )

        try:
            repository.update_name(found, None)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Non-string name update should be rejected."
            )

        print("NON-STRING FIELD SAFETY: PASS")


if __name__ == "__main__":
    main()