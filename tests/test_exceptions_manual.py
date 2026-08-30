import builtins

from core.exceptions import (
    CommandCenterError,
    MemorySystemError,
    ValidationError,
)


def main() -> None:
    # -------------------------------------------------
    # BASIC CONSTRUCTION
    # -------------------------------------------------

    error = ValidationError(
        "bad input",
        details={"field": "x"},
    )

    if str(error) != "bad input":
        raise RuntimeError(
            "str(error) should return the message."
        )

    if error.message != "bad input":
        raise RuntimeError(
            "message attribute is incorrect."
        )

    if error.details != {"field": "x"}:
        raise RuntimeError(
            "details attribute is incorrect."
        )

    if error.error_code != "VALIDATION_ERROR":
        raise RuntimeError(
            "error_code is incorrect."
        )

    print("BASIC CONSTRUCTION: PASS")

    # -------------------------------------------------
    # DEFAULT DETAILS
    # -------------------------------------------------

    no_details = CommandCenterError("plain message")

    if no_details.details != {}:
        raise RuntimeError(
            "details should default to an empty dict."
        )

    print("DEFAULT DETAILS: PASS")

    # -------------------------------------------------
    # NON-STRING MESSAGE (EXCEPTION-SAFETY)
    # -------------------------------------------------
    #
    # str(exc) must never itself raise, regardless of what
    # was passed as the message -- a broken __str__ on an
    # exception is catastrophic for any code that logs or
    # formats an already-raised error.
    # -------------------------------------------------

    for bad_message in (None, 123, ["not", "a", "string"]):
        error = CommandCenterError(bad_message)

        if not isinstance(error.message, str):
            raise RuntimeError(
                "message must always be coerced to a string, "
                f"got {type(error.message).__name__} for "
                f"{bad_message!r}."
            )

        try:
            rendered = str(error)
        except Exception as exc:
            raise RuntimeError(
                f"str(error) raised for message={bad_message!r}: "
                f"{type(exc).__name__}: {exc}"
            )

        if not isinstance(rendered, str):
            raise RuntimeError(
                "str(error) must return a string."
            )

    print("NON-STRING MESSAGE SAFETY: PASS")

    # -------------------------------------------------
    # MEMORYSYSTEMERROR DOES NOT SHADOW THE BUILTIN
    # -------------------------------------------------

    if MemorySystemError is builtins.MemoryError:
        raise RuntimeError(
            "MemorySystemError must not be the built-in "
            "MemoryError."
        )

    if not issubclass(
        MemorySystemError,
        CommandCenterError,
    ):
        raise RuntimeError(
            "MemorySystemError must inherit from "
            "CommandCenterError."
        )

    caught_builtin = False

    try:
        raise builtins.MemoryError("out of memory")
    except MemorySystemError:
        raise RuntimeError(
            "A real built-in MemoryError must not be caught "
            "by MemorySystemError."
        )
    except builtins.MemoryError:
        caught_builtin = True

    if not caught_builtin:
        raise RuntimeError(
            "The built-in MemoryError should still be catchable "
            "on its own."
        )

    print("MEMORYSYSTEMERROR ISOLATION: PASS")

    print()
    print("=" * 60)
    print("EXCEPTIONS: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
