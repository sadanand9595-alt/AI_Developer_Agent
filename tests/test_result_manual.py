from core.result import ErrorInfo, Result


def main() -> None:
    # -------------------------------------------------
    # RESULT.OK
    # -------------------------------------------------

    ok = Result.ok({"value": 1})

    if not ok.is_success():
        raise RuntimeError(
            "Result.ok() should be successful."
        )

    if ok.is_failure():
        raise RuntimeError(
            "Successful result must not report failure."
        )

    if ok.error is not None:
        raise RuntimeError(
            "Successful result must not carry error info."
        )

    if ok.require_data() != {"value": 1}:
        raise RuntimeError(
            "require_data() returned incorrect data."
        )

    print("RESULT.OK: PASS")

    # -------------------------------------------------
    # RESULT.OK WITH NO DATA
    # -------------------------------------------------

    empty_ok = Result.ok()

    if not empty_ok.is_success():
        raise RuntimeError(
            "Result.ok() with no data should still succeed."
        )

    if empty_ok.require_data() is not None:
        raise RuntimeError(
            "require_data() should return None when no data given."
        )

    print("RESULT.OK EMPTY: PASS")

    # -------------------------------------------------
    # RESULT.FAIL
    # -------------------------------------------------

    fail = Result.fail(
        "TEST_ERROR",
        "Something went wrong.",
        details={"field": "x"},
    )

    if fail.is_success():
        raise RuntimeError(
            "Result.fail() must not report success."
        )

    if not fail.is_failure():
        raise RuntimeError(
            "Result.fail() should report failure."
        )

    if fail.data is not None:
        raise RuntimeError(
            "Failed result must not carry data."
        )

    if fail.error.code != "TEST_ERROR":
        raise RuntimeError(
            "Error code is incorrect."
        )

    if fail.error.message != "Something went wrong.":
        raise RuntimeError(
            "Error message is incorrect."
        )

    if fail.error.details != {"field": "x"}:
        raise RuntimeError(
            "Error details are incorrect."
        )

    print("RESULT.FAIL: PASS")

    # -------------------------------------------------
    # FAIL WITHOUT DETAILS DEFAULTS TO EMPTY DICT
    # -------------------------------------------------

    no_details_fail = Result.fail("CODE", "message")

    if no_details_fail.error.details != {}:
        raise RuntimeError(
            "Missing details should default to an empty dict."
        )

    print("FAIL DEFAULT DETAILS: PASS")

    # -------------------------------------------------
    # REQUIRE_DATA RAISES ON FAILURE
    # -------------------------------------------------

    try:
        fail.require_data()
    except RuntimeError as exc:
        if str(exc) != "Something went wrong.":
            raise RuntimeError(
                "require_data() raised with the wrong message."
            )
    else:
        raise RuntimeError(
            "require_data() should raise on a failed result."
        )

    print("REQUIRE_DATA RAISES: PASS")

    # -------------------------------------------------
    # STATE CONSISTENCY (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------
    #
    # A "successful" Result carrying error information is
    # internally inconsistent: require_data() trusts
    # `success` alone and would otherwise silently return
    # None instead of surfacing the attached error. This
    # must be rejected at construction.
    # -------------------------------------------------

    try:
        Result(
            success=True,
            error=ErrorInfo(
                code="X",
                message="m",
            ),
        )
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "A successful Result with error info should be "
            "rejected."
        )

    print("STATE CONSISTENCY: PASS")

    print()
    print("=" * 60)
    print("RESULT: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
