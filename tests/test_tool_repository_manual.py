from uuid import uuid4

from core.types import ToolRiskLevel
from database.repositories.tool_repository import ToolRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        repository = ToolRepository(session)

        tool = repository.create(
            name=f"Test File Tool {uuid4()}",
            tool_type="filesystem",
            description="Test tool for repository verification.",
            version="1.0.0",
            risk_level=ToolRiskLevel.MEDIUM,
            permissions=[
                "read",
                "write",
            ],
            requires_approval=True,
        )

        print("CREATED:", tool.id, tool.name)
        print("RISK:", tool.risk_level)
        print("APPROVAL:", tool.requires_approval)

        found = repository.get_by_id(tool.id)

        if found is None:
            raise RuntimeError("Tool could not be read.")

        print("READ:", found.name)

        repository.mark_used(found)

        print(
            "LAST USED:",
            found.last_used_at is not None,
        )

        repository.disable(found)

        print("DISABLED:", found.is_enabled)

        repository.enable(found)

        print("ENABLED:", found.is_enabled)


if __name__ == "__main__":
    main()