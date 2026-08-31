from uuid import uuid4

from core.types import ToolRiskLevel
from database.session import session_scope
from services.approval_service import ApprovalService
from services.tool_service import ToolService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"approval-service-{uuid4()}@example.com",
            name="Approval Service Test User",
            password_hash="test-hash-not-used",
        )

        approval_service = ApprovalService(session)

        approval = approval_service.request_approval(
            user_id=user.id,
            action="execute_command",
            reason="Testing human approval workflow.",
            requested_operation="Run test command.",
            request_payload={
                "command": "echo test",
            },
        )

        print("CREATED:", approval.id)
        print("STATUS:", approval.status)
        print("ACTION:", approval.action)

        found = approval_service.get_approval(
            approval.id
        )

        if found is None:
            raise RuntimeError(
                "Approval request could not be retrieved."
            )

        print("READ:", found.action)

        pending = (
            approval_service.get_pending_approvals(
                user.id
            )
        )

        print(
            "PENDING:",
            len(pending),
        )

        approved = approval_service.approve(
            approval.id,
            reviewer_id=user.id,
            comment="Approved for testing.",
        )

        print(
            "APPROVED:",
            approved.status,
        )

        print(
            "REVIEWER:",
            approved.reviewed_by,
        )

        print(
            "COMMENT:",
            approved.reviewer_comment,
        )

        # -------------------------------------------------
        # APPROVAL <-> TOOL PARENT INTEGRITY
        # -------------------------------------------------
        #
        # An approval referencing a nonexistent tool_id must be
        # rejected with a clean ValueError, not an uncaught
        # database IntegrityError. A valid tool_id must still
        # work normally.
        # -------------------------------------------------

        tool_service = ToolService(session)

        tool = tool_service.register_tool(
            name=f"Approval Test Tool {uuid4()}",
            tool_type="filesystem",
            risk_level=ToolRiskLevel.HIGH,
        )

        tool_approval = approval_service.request_approval(
            user_id=user.id,
            action="use_tool",
            reason="Testing tool-linked approval.",
            requested_operation="Delete a file.",
            tool_id=tool.id,
        )

        if tool_approval.tool_id != tool.id:
            raise RuntimeError(
                "Approval should be linked to the tool."
            )

        print("APPROVAL WITH VALID TOOL: PASS")

        try:
            approval_service.request_approval(
                user_id=user.id,
                action="use_tool",
                reason="Should not be created.",
                requested_operation="Delete a file.",
                tool_id="nonexistent-tool-id",
            )
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Approval for a nonexistent tool should be "
                "rejected."
            )

        print("MISSING TOOL PROTECTION: PASS")


if __name__ == "__main__":
    main()