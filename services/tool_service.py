"""
Tool service for AI Command Center.

Contains business logic for registering and managing AI tools.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from core.types import ToolRiskLevel
from database.models.tool import Tool
from database.repositories.tool_repository import ToolRepository


class ToolService:
    """Business operations for AI tools."""

    def __init__(self, session: Session) -> None:
        self._repository = ToolRepository(session)

    def register_tool(
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
        """Register a new tool."""

        existing = self._repository.get_by_name(name)

        if existing is not None:
            raise ValueError(
                f"Tool already exists: {name}"
            )

        if (
            risk_level != ToolRiskLevel.READ_ONLY
            and not requires_approval
        ):
            requires_approval = True

        return self._repository.create(
            name=name,
            tool_type=tool_type,
            description=description,
            version=version,
            risk_level=risk_level,
            input_schema=input_schema,
            output_schema=output_schema,
            configuration=configuration,
            permissions=permissions,
            requires_approval=requires_approval,
        )

    def get_tool(
        self,
        tool_id: str,
    ) -> Tool | None:
        """Get a tool by ID."""

        return self._repository.get_by_id(tool_id)

    def get_tool_by_name(
        self,
        name: str,
    ) -> Tool | None:
        """Get a tool by name."""

        return self._repository.get_by_name(name)

    def list_enabled_tools(self) -> list[Tool]:
        """Return all enabled tools."""

        return self._repository.list_enabled()

    def list_tools_by_risk(
        self,
        risk_level: ToolRiskLevel,
    ) -> list[Tool]:
        """Return tools matching a risk level."""

        return self._repository.list_by_risk(
            risk_level
        )

    def enable_tool(
        self,
        tool_id: str,
    ) -> Tool:
        """Enable a tool."""

        tool = self._get_required_tool(tool_id)

        self._repository.enable(tool)

        return tool

    def disable_tool(
        self,
        tool_id: str,
    ) -> Tool:
        """Disable a tool."""

        tool = self._get_required_tool(tool_id)

        self._repository.disable(tool)

        return tool

    def mark_tool_used(
        self,
        tool_id: str,
    ) -> Tool:
        """Record tool usage."""

        tool = self._get_required_tool(tool_id)

        if not tool.is_enabled:
            raise ValueError(
                "Cannot use a disabled tool."
            )

        self._repository.mark_used(tool)

        return tool

    def requires_approval(
        self,
        tool_id: str,
    ) -> bool:
        """Return whether a tool requires human approval."""

        tool = self._get_required_tool(tool_id)

        return tool.requires_approval

    def _get_required_tool(
        self,
        tool_id: str,
    ) -> Tool:
        """Return a tool or raise a controlled error."""

        tool = self._repository.get_by_id(tool_id)

        if tool is None:
            raise ValueError("Tool not found.")

        return tool