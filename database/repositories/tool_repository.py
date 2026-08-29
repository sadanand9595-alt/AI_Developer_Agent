"""
Tool repository for AI Command Center.

Provides persistence operations for registered tools.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.types import ToolRiskLevel
from database.models.tool import Tool


class ToolRepository:
    """Persistence operations for tools."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        name: str,
        tool_type: str,
        description: str | None = None,
        version: str = "1.0.0",
        risk_level: ToolRiskLevel = ToolRiskLevel.READ_ONLY,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        configuration: dict | None = None,
        permissions: list[str] | None = None,
        requires_approval: bool = False,
    ) -> Tool:
        """Create and persist a new tool."""

        normalized_name = name.strip()
        normalized_type = tool_type.strip()

        if not normalized_name:
            raise ValueError("Tool name cannot be empty.")

        if not normalized_type:
            raise ValueError("Tool type cannot be empty.")

        if not version.strip():
            raise ValueError("Tool version cannot be empty.")

        tool = Tool(
            name=normalized_name,
            tool_type=normalized_type,
            description=description,
            version=version.strip(),
            risk_level=risk_level.value,
            input_schema=input_schema,
            output_schema=output_schema,
            configuration=configuration,
            permissions=permissions,
            requires_approval=requires_approval,
            is_enabled=True,
        )

        self._session.add(tool)
        self._session.flush()

        return tool

    def get_by_id(
        self,
        tool_id: str,
    ) -> Tool | None:
        """Return a tool by ID."""

        statement = select(Tool).where(
            Tool.id == tool_id
        )

        return self._session.scalar(statement)

    def get_by_name(
        self,
        name: str,
    ) -> Tool | None:
        """Return a tool by name."""

        statement = select(Tool).where(
            Tool.name == name.strip()
        )

        return self._session.scalar(statement)

    def list_enabled(self) -> list[Tool]:
        """Return all enabled tools."""

        statement = (
            select(Tool)
            .where(Tool.is_enabled.is_(True))
            .order_by(Tool.name.asc())
        )

        return list(
            self._session.scalars(statement).all()
        )

    def list_by_risk(
        self,
        risk_level: ToolRiskLevel,
    ) -> list[Tool]:
        """Return tools matching a risk level."""

        statement = (
            select(Tool)
            .where(
                Tool.risk_level == risk_level.value
            )
            .order_by(Tool.name.asc())
        )

        return list(
            self._session.scalars(statement).all()
        )

    def enable(
        self,
        tool: Tool,
    ) -> Tool:
        """Enable a tool."""

        tool.enable()
        self._session.flush()

        return tool

    def disable(
        self,
        tool: Tool,
    ) -> Tool:
        """Disable a tool."""

        tool.disable()
        self._session.flush()

        return tool

    def mark_used(
        self,
        tool: Tool,
    ) -> Tool:
        """Record tool usage."""

        tool.mark_used()
        self._session.flush()

        return tool