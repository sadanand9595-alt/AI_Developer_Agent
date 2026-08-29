from uuid import uuid4

from database.session import session_scope
from services.memory_service import MemoryService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"memory-service-{uuid4()}@example.com",
            name="Memory Service Test User",
        )

        memory_service = MemoryService(session)

        memory = memory_service.create_memory(
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

        found = memory_service.get_memory(memory.id)

        if found is None:
            raise RuntimeError("Memory could not be retrieved.")

        print("READ:", found.content)

        accessed = memory_service.access_memory(memory.id)

        print("ACCESSED:", accessed.last_accessed_at is not None)

        updated = memory_service.update_importance(
            memory.id,
            0.95,
        )

        print("UPDATED IMPORTANCE:", updated.importance)

        memories = memory_service.get_user_memories(user.id)

        print("USER MEMORIES:", len(memories))

        deactivated = memory_service.deactivate_memory(memory.id)

        print("ACTIVE:", deactivated.is_active)


if __name__ == "__main__":
    main()
