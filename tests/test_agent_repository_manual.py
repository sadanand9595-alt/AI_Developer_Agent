from uuid import uuid4

from database.repositories.agent_repository import AgentRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        repository = AgentRepository(session)

        agent = repository.create(
            name=f"Test Coding Agent {uuid4()}",
            agent_type="coding",
            description="Test agent for repository verification.",
            model_provider="local",
            model_name="test-model",
            capabilities=[
                "code_generation",
                "debugging",
                "testing",
            ],
            max_iterations=5,
        )

        print("CREATED:", agent.id, agent.name)
        print("STATUS:", agent.status)

        found = repository.get_by_id(agent.id)

        if found is None:
            raise RuntimeError("Agent could not be read.")

        print("READ:", found.name)

        repository.mark_active(found)

        print("ACTIVE:", found.status)

        repository.disable(found)

        print("DISABLED:", found.status)
        print("ENABLED:", found.is_enabled)


if __name__ == "__main__":
    main()