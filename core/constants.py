"""
Application-wide constants for AI Command Center.

Keep stable, non-secret values here. Runtime configuration
belongs in config.settings.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

PROJECT_NAME = "AI_COMMAND_CENTER"
PROJECT_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Agent execution
# ---------------------------------------------------------------------------

DEFAULT_MAX_AGENT_ITERATIONS = 10
DEFAULT_MAX_TOOL_CALLS = 20
DEFAULT_MAX_RETRY_ATTEMPTS = 3
DEFAULT_COMMAND_TIMEOUT_SECONDS = 120


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

DEFAULT_SESSION_TIMEOUT_MINUTES = 30

APPROVAL_REQUIRED_ACTIONS = frozenset(
    {
        "write",
        "delete",
        "external",
    }
)


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

MAX_TOOL_OUTPUT_LENGTH = 50_000
MAX_COMMAND_OUTPUT_LENGTH = 50_000


# ---------------------------------------------------------------------------
# Task execution
# ---------------------------------------------------------------------------

TASK_ID_PREFIX = "task"
EXECUTION_ID_PREFIX = "exec"
APPROVAL_ID_PREFIX = "approval"


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

API_PREFIX = "/api"
HEALTH_ENDPOINT = "/health"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/application.log"