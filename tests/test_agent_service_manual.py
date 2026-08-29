from uuid import uuid4

from database.session import session_scope
from services.agent_service import AgentService


def main() -> None:
    with session_scope() as session:
        service = AgentService(session)

        agent_name = f"Service Test Agent {uuid4()}"

        agent = service.register_agent(
            name=agent_name,
            agent_type="coding",
            description="Testing AgentService.",
            model_provider="local",
            model_name="test-model",
            capabilities=[
                "code_generation",
                "debugging",
                "testing",
            ],
            max_iterations=5,
        )

        print("REGISTERED:", agent.id, agent.name)
        print("STATUS:", agent.status)
        print("ENABLED:", agent.is_enabled)

        found = service.get_agent(agent.id)

        if found is None:
            raise RuntimeError(
                "Agent could not be retrieved."
            )

        print("READ:", found.name)

        by_name = service.get_agent_by_name(
            agent_name
        )

        if by_name is None:
            raise RuntimeError(
                "Agent could not be found by name."
            )

        print("NAME LOOKUP:", by_name.name)

        activated = service.activate_agent(
            agent.id
        )

        print(
            "ACTIVATED:",
            activated.status,
            activated.is_enabled,
        )

        active = service.mark_agent_active(
            agent.id
        )

        print(
            "RUNNING:",
            active.status,
        )

        disabled = service.disable_agent(
            agent.id
        )

        print(
            "DISABLED:",
            disabled.status,
            disabled.is_enabled,
        )

        enabled_agents = service.list_enabled_agents()

        print(
            "ENABLED AGENTS:",
            len(enabled_agents),
        )


if __name__ == "__main__":
    main()