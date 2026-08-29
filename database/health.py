"""
Database health checks for AI Command Center.
"""

from __future__ import annotations

from sqlalchemy import text

from core.result import Result
from database.connection import engine


def check_database() -> Result[dict[str, object]]:
    """
    Check whether the database connection is healthy.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return Result.ok(
            {
                "status": "healthy",
                "database": engine.url.get_backend_name(),
            }
        )

    except Exception as exc:
        return Result.fail(
            "DATABASE_CONNECTION_ERROR",
            "Database health check failed.",
            details={
                "error": str(exc),
            },
        )