"""
Exception handlers translating service-layer failures into the
existing Result-style error contract ({"error": {"code", "message"}})
used throughout core/ and services/.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain-exception -> HTTP response translation."""

    @app.exception_handler(ValueError)
    async def _handle_value_error(
        request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        # Every service in this codebase raises ValueError for a
        # controlled, expected failure (validation, missing/terminal
        # parent state, duplicate records, etc.) -- never for a
        # genuine server bug. Translating it to 400 here is what
        # lets every existing, already-audited service function as
        # an API handler with no changes to its own error handling.
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(
                "VALIDATION_ERROR",
                str(exc),
            ),
        )

    @app.exception_handler(LookupError)
    async def _handle_lookup_error(
        request: Request,
        exc: LookupError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_error_body(
                "NOT_FOUND",
                str(exc) or "Resource not found.",
            ),
        )
