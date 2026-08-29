from uuid import uuid4

from core.agent_runtime_manager import AgentRuntimeManager
from database.session import session_scope
from services.agent_runtime_service import AgentRuntimeService
from services.agent_service import AgentService


def main() -> None:
    with session_scope() as session:
        agent_service = AgentService(session)

        agent = agent_service.register_agent(
            name=f"Runtime Service Test Agent {uuid4()}",
            agent_type="coding",
            description="Testing agent runtime integration.",
            model_provider="local",
            model_name="test-model",
            capabilities=[
                "code_generation",
                "debugging",
            ],
            max_iterations=5,
        )

        print("AGENT CREATED:", agent.id)
        print("AGENT ENABLED:", agent.is_enabled)

        manager = AgentRuntimeManager()

        runtime_service = AgentRuntimeService(
            session,
            runtime_manager=manager,
        )

        runtime_result = runtime_service.get_runtime(
            agent.id
        )

        if runtime_result.is_failure():
            raise RuntimeError(
                runtime_result.error.message
            )

        runtime = runtime_result.require_data()

        print("RUNTIME CREATED:", runtime.agent_id)
        print("RUNTIME STATUS:", runtime.status.value)

        if runtime.agent_id != agent.id:
            raise RuntimeError(
                "Runtime agent ID does not match database agent."
            )

        print("AGENT → RUNTIME: PASS")

        if not runtime_service.has_runtime(
            agent.id
        ):
            raise RuntimeError(
                "Runtime should exist."
            )

        print("HAS RUNTIME: PASS")

        print(
            "RUNTIME COUNT:",
            runtime_service.runtime_count(),
        )

        same_result = runtime_service.get_runtime(
            agent.id
        )

        if same_result.is_failure():
            raise RuntimeError(
                "Existing runtime could not be retrieved."
            )

        same_runtime = same_result.require_data()

        if runtime is not same_runtime:
            raise RuntimeError(
                "Runtime manager should return the same instance."
            )

        print("SAME RUNTIME INSTANCE: PASS")

        removed = runtime_service.remove_runtime(
            agent.id
        )

        if removed.is_failure():
            raise RuntimeError(
                removed.error.message
            )

        print("RUNTIME REMOVED: PASS")

        if runtime_service.has_runtime(
            agent.id
        ):
            raise RuntimeError(
                "Runtime should no longer exist."
            )

        print("FINAL RUNTIME COUNT:", runtime_service.runtime_count())

        print()
        print("=" * 55)
        print("AGENT RUNTIME SERVICE: PASS")
        print("=" * 55)


if __name__ == "__main__":
    main()