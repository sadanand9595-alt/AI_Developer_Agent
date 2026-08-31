"""
Regression test: config.environment.validate_environment() must
refuse to start outside development with the default JWT secret
still in place.

Root cause: the API layer now signs and verifies real JWTs with
settings.jwt_secret. The documented default
("development-only-secret") is publicly known, so leaving it in
place in any non-development environment lets anyone forge a valid
token for any user (including an admin) without authenticating.
Live-reproduced by forging an admin token with the literal default
string and successfully calling a protected endpoint.
"""

from __future__ import annotations

import pytest

from config.environment import EnvironmentError as ConfigEnvironmentError
from config.environment import validate_environment
from config.settings import Settings


def _settings(**overrides: object) -> Settings:
    base = dict(
        app_name="x",
        app_env="development",
        app_host="127.0.0.1",
        app_port=8000,
        log_level="INFO",
        database_url="sqlite:///./data/command_center.db",
        ai_provider="ollama",
        ai_model="llama3.1",
        openai_api_key=None,
        anthropic_api_key=None,
        google_api_key=None,
        ollama_base_url="http://127.0.0.1:11434",
        jwt_secret="development-only-secret",
        jwt_access_expires_minutes=30,
        vector_db_path="./data/vector_store",
        workspace_root="./workspace",
        max_agent_iterations=10,
        max_tool_calls=20,
        command_timeout_seconds=120,
        max_retry_attempts=3,
        require_approval_for_write=True,
        require_approval_for_delete=True,
        require_approval_for_external_action=True,
    )
    base.update(overrides)
    return Settings(**base)


def test_development_with_default_secret_is_allowed() -> None:
    validate_environment(_settings(app_env="development"))


def test_production_with_default_secret_is_rejected() -> None:
    with pytest.raises(ConfigEnvironmentError):
        validate_environment(_settings(app_env="production"))


def test_production_with_real_secret_is_allowed() -> None:
    validate_environment(
        _settings(
            app_env="production",
            jwt_secret="a-real-random-secret-value",
        )
    )
