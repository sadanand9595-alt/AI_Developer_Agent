from uuid import uuid4

from database.repositories.memory_repository import (
    MemoryRepository,
)
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        user = user_repository.create(
            email=f"memory-{uuid4()}@example.com",
            name="Memory Test User",
            password_hash="test-hash-not-used",
        )

        repository = MemoryRepository(session)

        memory = repository.create(
            user_id=user.id,
            content="User prefers production-ready architecture.",
            memory_type="preference",
            source="test",
            metadata={
                "category": "development",
            },
            importance=0.8,
        )

        print("CREATED:", memory.id)
        print("TYPE:", memory.memory_type)
        print("IMPORTANCE:", memory.importance)

        found = repository.get_by_id(memory.id)

        if found is None:
            raise RuntimeError(
                "Memory could not be read."
            )

        print("READ:", found.content)

        repository.mark_accessed(found)

        print(
            "ACCESSED:",
            found.last_accessed_at is not None,
        )

        repository.update_importance(
            found,
            0.95,
        )

        print(
            "UPDATED IMPORTANCE:",
            found.importance,
        )

        memories = repository.list_by_user(
            user.id,
        )

        print(
            "USER MEMORIES:",
            len(memories),
        )

        repository.deactivate(found)

        print(
            "ACTIVE:",
            found.is_active,
        )


if __name__ == "__main__":
    main()