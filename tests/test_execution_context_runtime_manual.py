from core.execution_context_runtime import (
    ExecutionContextRuntime,
)


def main() -> None:
    runtime = ExecutionContextRuntime(
        context_id="runtime-context-001"
    )

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if not runtime.active:
        raise RuntimeError(
            "Runtime must start active."
        )

    if runtime.paused:
        raise RuntimeError(
            "Runtime must start unpaused."
        )

    if runtime.current_step is not None:
        raise RuntimeError(
            "No step should be active initially."
        )

    if runtime.completed_steps != 0:
        raise RuntimeError(
            "Completed steps must start at zero."
        )

    if runtime.failed_steps != 0:
        raise RuntimeError(
            "Failed steps must start at zero."
        )

    if runtime.variables != {}:
        raise RuntimeError(
            "Variables must start empty."
        )

    if runtime.stopped_at is not None:
        raise RuntimeError(
            "Runtime must not have a stop timestamp initially."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # START STEP
    # -------------------------------------------------

    runtime.start_step(
        "analyze"
    )

    if runtime.current_step != "analyze":
        raise RuntimeError(
            "Current step was not set."
        )

    print("START STEP: PASS")

    # -------------------------------------------------
    # COMPLETE STEP
    # -------------------------------------------------

    runtime.complete_step()

    if runtime.current_step is not None:
        raise RuntimeError(
            "Current step should be cleared."
        )

    if runtime.completed_steps != 1:
        raise RuntimeError(
            "Completed step count should be one."
        )

    print("COMPLETE STEP: PASS")

    # -------------------------------------------------
    # SECOND STEP + FAILURE
    # -------------------------------------------------

    runtime.start_step(
        "generate"
    )

    runtime.fail_step()

    if runtime.current_step is not None:
        raise RuntimeError(
            "Failed step should be cleared."
        )

    if runtime.failed_steps != 1:
        raise RuntimeError(
            "Failed step count should be one."
        )

    print("FAIL STEP: PASS")

    # -------------------------------------------------
    # VARIABLES
    # -------------------------------------------------

    runtime.set_variable(
        "attempt",
        1,
    )

    runtime.set_variable(
        "result",
        {
            "status": "ok",
        },
    )

    if runtime.get_variable(
        "attempt"
    ) != 1:
        raise RuntimeError(
            "Variable value is incorrect."
        )

    if runtime.get_variable(
        "missing"
    ) is not None:
        raise RuntimeError(
            "Missing variable should return None."
        )

    if runtime.get_variable(
        "missing",
        "default",
    ) != "default":
        raise RuntimeError(
            "Variable default was not returned."
        )

    print("SET/GET VARIABLES: PASS")

    # -------------------------------------------------
    # REMOVE VARIABLE
    # -------------------------------------------------

    removed = runtime.remove_variable(
        "attempt"
    )

    if not removed:
        raise RuntimeError(
            "Existing variable should be removed."
        )

    if runtime.get_variable(
        "attempt"
    ) is not None:
        raise RuntimeError(
            "Removed variable must not exist."
        )

    if runtime.remove_variable(
        "missing"
    ):
        raise RuntimeError(
            "Missing variable should not be removed."
        )

    print("REMOVE VARIABLE: PASS")

    # -------------------------------------------------
    # PAUSE
    # -------------------------------------------------

    runtime.pause()

    if not runtime.paused:
        raise RuntimeError(
            "Runtime should be paused."
        )

    print("PAUSE: PASS")

    # -------------------------------------------------
    # REPEATED PAUSE
    # -------------------------------------------------

    runtime.pause()

    if not runtime.paused:
        raise RuntimeError(
            "Repeated pause should remain safe."
        )

    print("IDEMPOTENT PAUSE: PASS")

    # -------------------------------------------------
    # RESUME
    # -------------------------------------------------

    runtime.resume()

    if runtime.paused:
        raise RuntimeError(
            "Runtime should be resumed."
        )

    print("RESUME: PASS")

    # -------------------------------------------------
    # REPEATED RESUME
    # -------------------------------------------------

    runtime.resume()

    if runtime.paused:
        raise RuntimeError(
            "Repeated resume should remain safe."
        )

    print("IDEMPOTENT RESUME: PASS")

    # -------------------------------------------------
    # SNAPSHOT
    # -------------------------------------------------

    snapshot = runtime.snapshot()

    if snapshot["context_id"] != (
        "runtime-context-001"
    ):
        raise RuntimeError(
            "Snapshot context ID is incorrect."
        )

    if snapshot["active"] is not True:
        raise RuntimeError(
            "Snapshot active state is incorrect."
        )

    if snapshot["paused"] is not False:
        raise RuntimeError(
            "Snapshot paused state is incorrect."
        )

    if snapshot["completed_steps"] != 1:
        raise RuntimeError(
            "Snapshot completed steps are incorrect."
        )

    if snapshot["failed_steps"] != 1:
        raise RuntimeError(
            "Snapshot failed steps are incorrect."
        )

    if snapshot["variables"] != {
        "result": {
            "status": "ok",
        }
    }:
        raise RuntimeError(
            "Snapshot variables are incorrect."
        )

    print("SNAPSHOT: PASS")

    # -------------------------------------------------
    # SNAPSHOT ISOLATION
    # -------------------------------------------------

    snapshot["variables"]["result"] = {
        "status": "modified"
    }

    if runtime.get_variable(
        "result"
    ) != {
        "status": "ok"
    }:
        raise RuntimeError(
            "Snapshot mutation must not modify runtime."
        )

    print("SNAPSHOT ISOLATION: PASS")

    # -------------------------------------------------
    # INVALID STEP
    # -------------------------------------------------

    try:
        runtime.start_step("   ")
    except ValueError:
        print("INVALID STEP: PASS")
    else:
        raise RuntimeError(
            "Empty step name should be rejected."
        )

    # -------------------------------------------------
    # COMPLETE WITHOUT STEP
    # -------------------------------------------------

    try:
        runtime.complete_step()
    except RuntimeError:
        print("NO ACTIVE STEP COMPLETE: PASS")
    else:
        raise RuntimeError(
            "Completing without active step should fail."
        )

    # -------------------------------------------------
    # FAIL WITHOUT STEP
    # -------------------------------------------------

    try:
        runtime.fail_step()
    except RuntimeError:
        print("NO ACTIVE STEP FAIL: PASS")
    else:
        raise RuntimeError(
            "Failing without active step should fail."
        )

    # -------------------------------------------------
    # STOP
    # -------------------------------------------------

    runtime.stop()

    if runtime.active:
        raise RuntimeError(
            "Runtime should be inactive after stop."
        )

    if runtime.paused:
        raise RuntimeError(
            "Stopped runtime must not remain paused."
        )

    if runtime.current_step is not None:
        raise RuntimeError(
            "Stopped runtime must not have an active step."
        )

    if runtime.stopped_at is None:
        raise RuntimeError(
            "Stopped timestamp must be populated."
        )

    print("STOP: PASS")

    # -------------------------------------------------
    # IDEMPOTENT STOP
    # -------------------------------------------------

    stopped_at = runtime.stopped_at

    runtime.stop()

    if runtime.stopped_at != stopped_at:
        raise RuntimeError(
            "Repeated stop must preserve stop timestamp."
        )

    print("IDEMPOTENT STOP: PASS")

    # -------------------------------------------------
    # OPERATIONS AFTER STOP
    # -------------------------------------------------

    try:
        runtime.start_step(
            "after-stop"
        )
    except RuntimeError:
        print("STOPPED STEP PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Step operation after stop should fail."
        )

    try:
        runtime.set_variable(
            "after_stop",
            True,
        )
    except RuntimeError:
        print("STOPPED VARIABLE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Variable mutation after stop should fail."
        )

    try:
        runtime.pause()
    except RuntimeError:
        print("STOPPED PAUSE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Pause after stop should fail."
        )

    try:
        runtime.resume()
    except RuntimeError:
        print("STOPPED RESUME PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Resume after stop should fail."
        )

    try:
        runtime.remove_variable(
            "result"
        )
    except RuntimeError:
        print("STOPPED REMOVE VARIABLE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Removing a variable after stop should fail."
        )

    if runtime.get_variable(
        "result"
    ) != {
        "status": "ok"
    }:
        raise RuntimeError(
            "Variable must be unchanged after a rejected "
            "post-stop removal."
        )

    # -------------------------------------------------
    # EMPTY CONTEXT ID
    # -------------------------------------------------

    try:
        ExecutionContextRuntime(
            context_id="   "
        )
    except ValueError:
        print("EMPTY CONTEXT ID: PASS")
    else:
        raise RuntimeError(
            "Empty context ID should be rejected."
        )

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT RUNTIME: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()