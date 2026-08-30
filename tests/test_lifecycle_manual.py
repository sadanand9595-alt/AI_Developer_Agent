from core.exceptions import ValidationError
from core.lifecycle import AgentLifecycle, TaskLifecycle
from core.types import AgentStatus, TaskStatus


def main() -> None:
    # -------------------------------------------------
    # VALID TRANSITIONS
    # -------------------------------------------------

    if not AgentLifecycle.can_transition(
        AgentStatus.IDLE,
        AgentStatus.PLANNING,
    ):
        raise RuntimeError(
            "IDLE -> PLANNING should be allowed."
        )

    if (
        AgentLifecycle.transition(
            AgentStatus.IDLE,
            AgentStatus.PLANNING,
        )
        != AgentStatus.PLANNING
    ):
        raise RuntimeError(
            "transition() should return the target status."
        )

    if not TaskLifecycle.can_transition(
        TaskStatus.PENDING,
        TaskStatus.PLANNING,
    ):
        raise RuntimeError(
            "PENDING -> PLANNING should be allowed."
        )

    print("VALID TRANSITIONS: PASS")

    # -------------------------------------------------
    # INVALID TRANSITION (VALID ENUM MEMBERS)
    # -------------------------------------------------

    if AgentLifecycle.can_transition(
        AgentStatus.IDLE,
        AgentStatus.ERROR,
    ):
        raise RuntimeError(
            "IDLE -> ERROR should not be allowed."
        )

    try:
        AgentLifecycle.transition(
            AgentStatus.IDLE,
            AgentStatus.ERROR,
        )
    except ValidationError:
        print("INVALID TRANSITION: PASS")
    else:
        raise RuntimeError(
            "Invalid transition should raise ValidationError."
        )

    # -------------------------------------------------
    # TERMINAL STATE
    # -------------------------------------------------

    if TaskLifecycle.can_transition(
        TaskStatus.COMPLETED,
        TaskStatus.RUNNING,
    ):
        raise RuntimeError(
            "COMPLETED must be terminal."
        )

    try:
        TaskLifecycle.transition(
            TaskStatus.COMPLETED,
            TaskStatus.RUNNING,
        )
    except ValidationError:
        print("TERMINAL STATE: PASS")
    else:
        raise RuntimeError(
            "Transition out of a terminal state should fail."
        )

    # -------------------------------------------------
    # MALFORMED INPUT (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------
    #
    # can_transition() must return False, and transition()
    # must raise ValidationError, for non-enum current/target
    # values (plain strings, None, unhashable types) rather
    # than crashing with an unrelated AttributeError/TypeError.
    # -------------------------------------------------

    malformed_values = (
        "idle",
        None,
        123,
        ["not", "hashable"],
    )

    for bad_value in malformed_values:
        try:
            result = AgentLifecycle.can_transition(
                bad_value,
                AgentStatus.IDLE,
            )
        except Exception as exc:
            raise RuntimeError(
                "can_transition raised unexpected exception "
                f"for current={bad_value!r}: "
                f"{type(exc).__name__}: {exc}"
            )

        if result is not False:
            raise RuntimeError(
                f"can_transition should return False for "
                f"current={bad_value!r}."
            )

        try:
            AgentLifecycle.transition(
                bad_value,
                AgentStatus.IDLE,
            )
        except ValidationError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "transition raised unexpected exception for "
                f"current={bad_value!r}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"transition should reject current={bad_value!r}."
            )

        # Same checks with the malformed value as the target.
        try:
            result = TaskLifecycle.can_transition(
                TaskStatus.PENDING,
                bad_value,
            )
        except Exception as exc:
            raise RuntimeError(
                "can_transition raised unexpected exception "
                f"for target={bad_value!r}: "
                f"{type(exc).__name__}: {exc}"
            )

        if result is not False:
            raise RuntimeError(
                f"can_transition should return False for "
                f"target={bad_value!r}."
            )

        try:
            TaskLifecycle.transition(
                TaskStatus.PENDING,
                bad_value,
            )
        except ValidationError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "transition raised unexpected exception for "
                f"target={bad_value!r}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"transition should reject target={bad_value!r}."
            )

    print("MALFORMED INPUT SAFETY: PASS")

    print()
    print("=" * 60)
    print("LIFECYCLE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
