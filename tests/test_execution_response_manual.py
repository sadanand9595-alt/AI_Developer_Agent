from core.execution_response import ExecutionResponse


def main() -> None:
    execution_id = "execution-001"
    plan_id = "plan-001"

    # -------------------------------------------------
    # SUCCESS RESPONSE
    # -------------------------------------------------

    response = ExecutionResponse.success_response(
        execution_id=execution_id,
        plan_id=plan_id,
        output={
            "status": "completed",
            "files": 5,
        },
        metadata={
            "duration_ms": 1250,
            "engine": "execution-engine",
        },
    )

    print("SUCCESS:", response.success)
    print("EXECUTION ID:", response.execution_id)
    print("PLAN ID:", response.plan_id)
    print("OUTPUT:", response.output)
    print("METADATA:", response.metadata)

    if not response.is_success():
        raise RuntimeError(
            "Success response should be successful."
        )

    if response.is_failure():
        raise RuntimeError(
            "Success response cannot be a failure."
        )

    if response.execution_id != execution_id:
        raise RuntimeError(
            "Execution ID was not stored correctly."
        )

    if response.plan_id != plan_id:
        raise RuntimeError(
            "Plan ID was not stored correctly."
        )

    if response.require_output()["files"] != 5:
        raise RuntimeError(
            "Output was not stored correctly."
        )

    if response.get_metadata(
        "engine"
    ) != "execution-engine":
        raise RuntimeError(
            "Metadata was not stored correctly."
        )

    print("SUCCESS RESPONSE: PASS")
    print("OUTPUT ACCESS: PASS")
    print("METADATA: PASS")

    # -------------------------------------------------
    # FAILURE RESPONSE
    # -------------------------------------------------

    failure = ExecutionResponse.failure_response(
        execution_id="execution-002",
        plan_id="plan-002",
        code="ACTION_FAILED",
        message="Code generation failed.",
        details={
            "action": "generate_code",
            "step": 3,
        },
        metadata={
            "retryable": True,
        },
    )

    print("FAILURE:", failure.success)
    print("FAILURE CODE:", failure.error.code)
    print("FAILURE MESSAGE:", failure.error.message)
    print("FAILURE DETAILS:", failure.error.details)

    if not failure.is_failure():
        raise RuntimeError(
            "Failure response should be a failure."
        )

    if failure.is_success():
        raise RuntimeError(
            "Failure response cannot be successful."
        )

    if failure.error.code != "ACTION_FAILED":
        raise RuntimeError(
            "Incorrect failure code."
        )

    if failure.error.details.get(
        "action"
    ) != "generate_code":
        raise RuntimeError(
            "Failure details were not stored."
        )

    if failure.get_metadata(
        "retryable"
    ) is not True:
        raise RuntimeError(
            "Failure metadata was not stored."
        )

    print("FAILURE RESPONSE: PASS")
    print("ERROR DETAILS: PASS")
    print("FAILURE METADATA: PASS")

    # -------------------------------------------------
    # REQUIRE OUTPUT ON FAILURE
    # -------------------------------------------------

    try:
        failure.require_output()
    except RuntimeError as exc:
        print(
            "REQUIRE OUTPUT FAILURE:",
            str(exc),
        )
        print("FAILURE GUARD: PASS")
    else:
        raise RuntimeError(
            "require_output() must fail for failed response."
        )

    # -------------------------------------------------
    # INVALID EXECUTION ID
    # -------------------------------------------------

    try:
        ExecutionResponse.success_response(
            execution_id="   ",
            output="invalid",
        )
    except ValueError:
        print("INVALID EXECUTION ID: PASS")
    else:
        raise RuntimeError(
            "Empty execution ID should be rejected."
        )

    # -------------------------------------------------
    # INVALID ERROR CODE
    # -------------------------------------------------

    try:
        ExecutionResponse.failure_response(
            execution_id="execution-003",
            code="   ",
            message="Failure",
        )
    except ValueError:
        print("INVALID ERROR CODE: PASS")
    else:
        raise RuntimeError(
            "Empty error code should be rejected."
        )

    # -------------------------------------------------
    # INVALID ERROR MESSAGE
    # -------------------------------------------------

    try:
        ExecutionResponse.failure_response(
            execution_id="execution-004",
            code="TEST_ERROR",
            message="   ",
        )
    except ValueError:
        print("INVALID ERROR MESSAGE: PASS")
    else:
        raise RuntimeError(
            "Empty error message should be rejected."
        )

    for bad_kwargs in (
        {"execution_id": 123},
    ):
        try:
            ExecutionResponse.success_response(**bad_kwargs)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                f"Non-string field {bad_kwargs!r} should be rejected."
            )

    for bad_kwargs in (
        {"execution_id": 123, "code": "c", "message": "m"},
        {"execution_id": "e1", "code": 123, "message": "m"},
        {"execution_id": "e1", "code": "c", "message": 123},
    ):
        try:
            ExecutionResponse.failure_response(**bad_kwargs)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                f"Non-string field {bad_kwargs!r} should be rejected."
            )

    print("NON-STRING FIELD SAFETY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION RESPONSE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()