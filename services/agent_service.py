"""
Agent service for AI Command Center.

Contains business logic for registering and managing AI agents.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.agent import Agent
from database.repositories.agent_repository import AgentRepository


class AgentService:
    """Business operations for AI agents."""

    def __init__(self, session: Session) -> None:
        self._repository = AgentRepository(session)

    def register_agent(
        self,
        *,
        name: str,
        agent_type: str,
        description: str | None = None,
        model_provider: str | None = None,
        model_name: str | None = None,
        capabilities: list[str] | None = None,
        configuration: dict | None = None,
        max_iterations: int = 10,
    ) -> Agent:
        """Register a new AI agent."""

        existing = self._repository.get_by_name(name)

        if existing is not None:
            raise ValueError(
                f"Agent already exists: {name}"
            )

        return self._repository.create(
            name=name,
            agent_type=agent_type,
            description=description,
            model_provider=model_provider,
            model_name=model_name,
            capabilities=capabilities,
            configuration=configuration,
            max_iterations=max_iterations,
        )

    def get_agent(
        self,
        agent_id: str,
    ) -> Agent | None:
        """Get an agent by ID."""

        return self._repository.get_by_id(agent_id)

    def get_agent_by_name(
        self,
        name: str,
    ) -> Agent | None:
        """Get an agent by name."""

        return self._repository.get_by_name(name)

    def list_enabled_agents(self) -> list[Agent]:
        """Return all enabled agents."""

        return self._repository.list_enabled()

    def list_agents_by_type(
        self,
        agent_type: str,
    ) -> list[Agent]:
        """Return agents of a specific type."""

        return self._repository.list_by_type(
            agent_type
        )

    def activate_agent(
        self,
        agent_id: str,
    ) -> Agent:
        """Activate an agent."""

        agent = self._get_required_agent(agent_id)

        self._repository.activate(agent)

        return agent

    def disable_agent(
        self,
        agent_id: str,
    ) -> Agent:
        """Disable an agent."""

        agent = self._get_required_agent(agent_id)

        self._repository.disable(agent)

        return agent

    def mark_agent_active(
        self,
        agent_id: str,
    ) -> Agent:
        """Mark an agent as currently active."""

        agent = self._get_required_agent(agent_id)

        if not agent.is_enabled:
            raise ValueError(
                "Cannot activate a disabled agent."
            )

        self._repository.mark_active(agent)

        return agent

    def _get_required_agent(
        self,
        agent_id: str,
    ) -> Agent:
        """Return an agent or raise a controlled error."""

        agent = self._repository.get_by_id(agent_id)

        if agent is None:
            raise ValueError("Agent not found.")

        return agent