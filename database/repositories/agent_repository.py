"""
Agent repository for AI Command Center.

Provides persistence operations for registered AI agents.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.types import AgentStatus
from database.models.agent import Agent


class AgentRepository:
    """Persistence operations for AI agents."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
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
        """Create and persist a new agent."""

        normalized_name = name.strip()
        normalized_type = agent_type.strip()

        if not normalized_name:
            raise ValueError("Agent name cannot be empty.")

        if not normalized_type:
            raise ValueError(
                "Agent type cannot be empty."
            )

        if max_iterations < 1:
            raise ValueError(
                "max_iterations must be at least 1."
            )

        agent = Agent(
            name=normalized_name,
            agent_type=normalized_type,
            description=description,
            model_provider=model_provider,
            model_name=model_name,
            capabilities=capabilities,
            configuration=configuration,
            max_iterations=max_iterations,
            status=AgentStatus.IDLE.value,
            is_enabled=True,
        )

        self._session.add(agent)
        self._session.flush()

        return agent

    def get_by_id(
        self,
        agent_id: str,
    ) -> Agent | None:
        """Return an agent by ID."""

        statement = select(Agent).where(
            Agent.id == agent_id
        )

        return self._session.scalar(statement)

    def get_by_name(
        self,
        name: str,
    ) -> Agent | None:
        """Return an agent by name."""

        statement = select(Agent).where(
            Agent.name == name.strip()
        )

        return self._session.scalar(statement)

    def list_enabled(self) -> list[Agent]:
        """Return all enabled agents."""

        statement = (
            select(Agent)
            .where(Agent.is_enabled.is_(True))
            .order_by(Agent.name.asc())
        )

        return list(
            self._session.scalars(statement).all()
        )

    def list_by_type(
        self,
        agent_type: str,
    ) -> list[Agent]:
        """Return agents matching an agent type."""

        statement = (
            select(Agent)
            .where(
                Agent.agent_type == agent_type.strip()
            )
            .order_by(Agent.name.asc())
        )

        return list(
            self._session.scalars(statement).all()
        )

    def activate(
        self,
        agent: Agent,
    ) -> Agent:
        """Activate an agent."""

        agent.activate()
        self._session.flush()

        return agent

    def disable(
        self,
        agent: Agent,
    ) -> Agent:
        """Disable an agent."""

        agent.disable()
        self._session.flush()

        return agent

    def mark_active(
        self,
        agent: Agent,
    ) -> Agent:
        """Record agent activity."""

        agent.mark_active()
        self._session.flush()

        return agent