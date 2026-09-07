"""
Application settings for AI Command Center.

All runtime configuration is loaded from environment variables
with safe development defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable safely."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable safely."""
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {name!r} must be an integer."
        ) from exc


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application configuration."""

    app_name: str
    app_env: str
    app_host: str
    app_port: int

    log_level: str

    database_url: str

    ai_provider: str
    ai_model: str

    openai_api_key: str | None
    anthropic_api_key: str | None
    google_api_key: str | None

    ollama_base_url: str

    jwt_secret: str
    jwt_access_expires_minutes: int

    vector_db_path: str
    workspace_root: str

    max_agent_iterations: int
    max_tool_calls: int
    command_timeout_seconds: int
    max_retry_attempts: int

    require_approval_for_write: bool
    require_approval_for_delete: bool
    require_approval_for_external_action: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load application settings once and cache them.

    The cache prevents repeatedly reading environment variables
    throughout the application lifecycle.
    """

    return Settings(
        app_name=os.getenv(
            "APP_NAME",
            "AI_COMMAND_CENTER",
        ),
        app_env=os.getenv(
            "APP_ENV",
            "development",
        ),
        app_host=os.getenv(
            "APP_HOST",
            "127.0.0.1",
        ),
        app_port=_get_int(
            "APP_PORT",
            8000,
        ),
        log_level=os.getenv(
            "LOG_LEVEL",
            "INFO",
        ),
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./data/command_center.db",
        ),
        ai_provider=os.getenv(
            "AI_PROVIDER",
            "ollama",
        ),
        ai_model=os.getenv(
            "AI_MODEL",
            "llama3.1",
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        google_api_key=os.getenv("GOOGLE_API_KEY") or None,
        ollama_base_url=os.getenv(
            "OLLAMA_BASE_URL",
            "http://127.0.0.1:11434",
        ),
        jwt_secret=os.getenv(
            "JWT_SECRET",
            "development-only-secret",
        ),
        jwt_access_expires_minutes=_get_int(
            "JWT_ACCESS_EXPIRES_MINUTES",
            30,
        ),
        vector_db_path=os.getenv(
            "VECTOR_DB_PATH",
            "./data/vector_store",
        ),
        workspace_root=os.getenv(
            "WORKSPACE_ROOT",
            "./workspace",
        ),
        max_agent_iterations=_get_int(
            "MAX_AGENT_ITERATIONS",
            10,
        ),
        max_tool_calls=_get_int(
            "MAX_TOOL_CALLS",
            20,
        ),
        command_timeout_seconds=_get_int(
            "COMMAND_TIMEOUT_SECONDS",
            120,
        ),
        max_retry_attempts=_get_int(
            "MAX_RETRY_ATTEMPTS",
            3,
        ),
        require_approval_for_write=_get_bool(
            "REQUIRE_APPROVAL_FOR_WRITE",
            True,
        ),
        require_approval_for_delete=_get_bool(
            "REQUIRE_APPROVAL_FOR_DELETE",
            True,
        ),
        require_approval_for_external_action=_get_bool(
            "REQUIRE_APPROVAL_FOR_EXTERNAL_ACTION",
            True,
        ),
    )


settings = get_settings()