"""
Agent runtime service for AI Command Center.

Connects persistent agent records with in-memory runtime instances.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from core.agent_runtime import AgentRuntime
from core.agent_runtime_manager import AgentRuntimeManager
from core.result import Result
from database.repositories.agent_repository import AgentRepository


class AgentRuntimeService:
    """Coordinate persistent agents and runtime instances."""

    def __init__(
        self,
        session: Session,
        runtime_manager: AgentRuntimeManager | None = None,
    ) -> None:
        self._repository = AgentRepository(session)
        self._runtime_manager = (
            runtime_manager
            if runtime_manager is not None
            else AgentRuntimeManager()
        )

    def get_runtime(
        self,
        agent_id: str,
    ) -> Result[AgentRuntime]:
        """Return the runtime for a registered agent."""

        agent = self._repository.get_by_id(agent_id)

        if agent is None:
            return Result.fail(
                "AGENT_NOT_FOUND",
                "Agent was not found.",
                details={
                    "agent_id": agent_id,
                },
            )

        if not agent.is_enabled:
            return Result.fail(
                "AGENT_DISABLED",
                "Agent is disabled.",
                details={
                    "agent_id": agent_id,
                },
            )

        return self._runtime_manager.get_or_create(
            agent.id
        )

    def activate_runtime(
        self,
        agent_id: str,
    ) -> Result[AgentRuntime]:
        """Validate the persistent agent and return its runtime."""

        runtime_result = self.get_runtime(agent_id)

        if runtime_result.is_failure():
            return runtime_result

        runtime = runtime_result.require_data()

        if runtime.status.value == "disabled":
            return Result.fail(
                "RUNTIME_DISABLED",
                "Agent runtime is disabled.",
                details={
                    "agent_id": agent_id,
                },
            )

        return Result.ok(runtime)

    def remove_runtime(
        self,
        agent_id: str,
    ) -> Result[None]:
        """Remove an idle runtime."""

        return self._runtime_manager.remove(
            agent_id
        )

    def has_runtime(
        self,
        agent_id: str,
    ) -> bool:
        """Return whether a runtime exists."""

        return self._runtime_manager.contains(
            agent_id
        )

    def runtime_count(self) -> int:
        """Return the number of active runtime instances."""

        return self._runtime_manager.count()

    @property
    def runtime_manager(
        self,
    ) -> AgentRuntimeManager:
        """Return the underlying runtime manager."""

        return self._runtime_manager