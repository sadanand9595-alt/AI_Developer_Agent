from core.agent_runtime import AgentRuntime
from core.context import ExecutionContext
from core.result import Result
from core.types import AgentStatus


def main() -> None:
    context = ExecutionContext.create(
        user_id="test-user",
        task_id="test-task",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER",
        permissions={
            "read",
            "write",
            "execute",
        },
    )

    runtime = AgentRuntime(
        agent_id="test-agent"
    )

    print("INITIAL:", runtime.status.value)

    if runtime.status != AgentStatus.IDLE:
        raise RuntimeError(
            "Agent must start in IDLE state."
        )

    result = runtime.execute(
        context=context,
        operation=lambda ctx: Result.ok(
            {
                "message": "Agent execution successful.",
                "agent_id": str(ctx.agent_id),
            }
        ),
    )

    print(
        "EXECUTION SUCCESS:",
        result.result.success,
    )

    print(
        "RESULT:",
        result.result.data,
    )

    print(
        "FINAL STATUS:",
        result.status.value,
    )

    if not result.result.success:
        raise RuntimeError(
            "Expected successful agent execution."
        )

    if result.status != AgentStatus.IDLE:
        raise RuntimeError(
            "Agent should return to IDLE after success."
        )

    # Failure path
    failed_runtime = AgentRuntime(
        agent_id="failure-test-agent"
    )

    failure = failed_runtime.execute(
        context=context,
        operation=lambda ctx: Result.fail(
            "TEST_FAILURE",
            "Simulated agent failure.",
        ),
    )

    print(
        "FAILURE RESULT:",
        failure.result.success,
    )

    print(
        "FAILURE STATUS:",
        failure.status.value,
    )

    if failure.result.success:
        raise RuntimeError(
            "Expected failed agent execution."
        )

    if failure.status != AgentStatus.ERROR:
        raise RuntimeError(
            "Failed execution should move agent to ERROR."
        )

    print("SUCCESS PATH: PASS")
    print("FAILURE PATH: PASS")

    # -------------------------------------------------
    # NON-STRING AGENT ID (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------

    for bad_agent_id in (None, 123, ["not", "a", "string"]):
        try:
            AgentRuntime(agent_id=bad_agent_id)
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "AgentRuntime() raised unexpected exception for "
                f"agent_id={bad_agent_id!r}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"Non-string agent_id {bad_agent_id!r} should "
                "be rejected."
            )

    print("NON-STRING AGENT ID: PASS")

    # -------------------------------------------------
    # INVALID CONTEXT TYPE
    # -------------------------------------------------
    #
    # execute() must reject a non-ExecutionContext with a
    # clear TypeError and leave the runtime in a stable
    # (unchanged) lifecycle state, not raise an unrelated
    # AttributeError mid-transition.
    # -------------------------------------------------

    type_check_runtime = AgentRuntime(
        agent_id="type-check-agent"
    )

    status_before = type_check_runtime.status

    try:
        type_check_runtime.execute(
            context="not-a-context",
            operation=lambda ctx: Result.ok(1),
        )
    except TypeError:
        pass
    except Exception as exc:
        raise RuntimeError(
            "execute() raised unexpected exception for an "
            f"invalid context: {type(exc).__name__}: {exc}"
        )
    else:
        raise RuntimeError(
            "Invalid context type should be rejected."
        )

    if type_check_runtime.status != status_before:
        raise RuntimeError(
            "Runtime status must remain unchanged when "
            "execute() rejects an invalid context."
        )

    print("INVALID CONTEXT TYPE: PASS")

    print("AGENT RUNTIME: PASS")


if __name__ == "__main__":
    main()