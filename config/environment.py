"""
Environment bootstrap utilities for AI Command Center.

This module validates the runtime environment and prepares
required local directories before the application starts.
"""

from __future__ import annotations

from pathlib import Path

from config.settings import Settings


class EnvironmentError(RuntimeError):
    """Raised when the application environment is invalid."""


def validate_environment(settings: Settings) -> None:
    """
    Validate critical runtime configuration.

    Raises:
        EnvironmentError: If a required configuration value is invalid.
    """

    if not settings.app_name.strip():
        raise EnvironmentError("APP_NAME cannot be empty.")

    if not settings.app_host.strip():
        raise EnvironmentError("APP_HOST cannot be empty.")

    if not 1 <= settings.app_port <= 65535:
        raise EnvironmentError(
            f"APP_PORT must be between 1 and 65535, "
            f"got {settings.app_port}."
        )

    if not settings.ai_provider.strip():
        raise EnvironmentError("AI_PROVIDER cannot be empty.")

    if not settings.ai_model.strip():
        raise EnvironmentError("AI_MODEL cannot be empty.")

    if settings.max_agent_iterations < 1:
        raise EnvironmentError(
            "MAX_AGENT_ITERATIONS must be at least 1."
        )

    if settings.max_tool_calls < 1:
        raise EnvironmentError(
            "MAX_TOOL_CALLS must be at least 1."
        )

    if settings.command_timeout_seconds < 1:
        raise EnvironmentError(
            "COMMAND_TIMEOUT_SECONDS must be at least 1."
        )

    if settings.max_retry_attempts < 0:
        raise EnvironmentError(
            "MAX_RETRY_ATTEMPTS cannot be negative."
        )

    # The API layer signs and verifies JWTs with this secret. The
    # documented default is explicitly dev-only; if it is still in
    # place outside development, anyone can forge a token for any
    # user (including an admin) without ever authenticating, since
    # the default value is publicly known.
    if (
        settings.app_env.strip().lower() != "development"
        and settings.jwt_secret == "development-only-secret"
    ):
        raise EnvironmentError(
            "JWT_SECRET must be set to a real secret outside "
            "the development environment."
        )


def ensure_directories(settings: Settings) -> None:
    """
    Create application directories that are required at runtime.
    """

    database_path = _extract_sqlite_path(settings.database_url)

    if database_path is not None:
        database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    vector_db_path = Path(settings.vector_db_path)
    vector_db_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    workspace_root = Path(settings.workspace_root)
    workspace_root.mkdir(
        parents=True,
        exist_ok=True,
    )


def _extract_sqlite_path(database_url: str) -> Path | None:
    """
    Extract a local SQLite database path.

    Only local SQLite URLs are handled here. Other database
    engines will be handled by the database layer later.
    """

    prefix = "sqlite:///"

    if not database_url.startswith(prefix):
        return None

    raw_path = database_url[len(prefix):].strip()

    if not raw_path:
        raise EnvironmentError(
            "SQLite DATABASE_URL must contain a database path."
        )

    path = Path(raw_path)

    if not path.is_absolute():
        path = Path.cwd() / path

    return path


def bootstrap_environment(settings: Settings) -> None:
    """
    Validate configuration and prepare required directories.
    """

    validate_environment(settings)
    ensure_directories(settings)