from uuid import uuid4

from core.types import ToolRiskLevel
from database.session import session_scope
from services.tool_service import ToolService


def main() -> None:
    with session_scope() as session:
        service = ToolService(session)

        tool_name = f"Service Test Tool {uuid4()}"

        tool = service.register_tool(
            name=tool_name,
            tool_type="filesystem",
            description="Testing ToolService.",
            version="1.0.0",
            risk_level=ToolRiskLevel.MEDIUM,
            permissions=[
                "read",
                "write",
            ],
            requires_approval=False,
        )

        print("REGISTERED:", tool.id, tool.name)
        print("RISK:", tool.risk_level)
        print("APPROVAL:", tool.requires_approval)
        print("ENABLED:", tool.is_enabled)

        found = service.get_tool(tool.id)

        if found is None:
            raise RuntimeError(
                "Tool could not be retrieved."
            )

        print("READ:", found.name)

        by_name = service.get_tool_by_name(
            tool_name
        )

        if by_name is None:
            raise RuntimeError(
                "Tool could not be found by name."
            )

        print("NAME LOOKUP:", by_name.name)

        approval_required = service.requires_approval(
            tool.id
        )

        print(
            "REQUIRES APPROVAL:",
            approval_required,
        )

        used = service.mark_tool_used(
            tool.id
        )

        print(
            "USED:",
            used.last_used_at is not None,
        )

        disabled = service.disable_tool(
            tool.id
        )

        print(
            "DISABLED:",
            disabled.is_enabled,
        )

        enabled = service.enable_tool(
            tool.id
        )

        print(
            "ENABLED:",
            enabled.is_enabled,
        )

        enabled_tools = service.list_enabled_tools()

        print(
            "ENABLED TOOLS:",
            len(enabled_tools),
        )


if __name__ == "__main__":
    main()