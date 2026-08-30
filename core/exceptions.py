"""
Standard exception hierarchy for AI Command Center.

All application-specific exceptions should inherit from
CommandCenterError so that the API, worker, agents, and
self-correction system can handle failures consistently.
"""

from __future__ import annotations


class CommandCenterError(Exception):
    """Base exception for the entire application."""

    error_code = "COMMAND_CENTER_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)

        # ``message`` is coerced to a string so that ``__str__`` can
        # never itself raise (a non-string message would otherwise
        # cause str(exc)/f"{exc}" to raise TypeError, which is
        # catastrophic when it happens inside error-handling code
        # such as logging an already-raised exception).
        self.message = (
            message
            if isinstance(message, str)
            else str(message)
        )

        self.details = details or {}

    def __str__(self) -> str:
        return self.message


class ConfigurationError(CommandCenterError):
    """Raised when application configuration is invalid."""

    error_code = "CONFIGURATION_ERROR"


class ValidationError(CommandCenterError):
    """Raised when input or output validation fails."""

    error_code = "VALIDATION_ERROR"


class AuthenticationError(CommandCenterError):
    """Raised when authentication fails."""

    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(CommandCenterError):
    """Raised when a user or agent lacks permission."""

    error_code = "AUTHORIZATION_ERROR"


class ApprovalRequiredError(CommandCenterError):
    """Raised when an action requires human approval."""

    error_code = "APPROVAL_REQUIRED"


class AgentError(CommandCenterError):
    """Base exception for agent-related failures."""

    error_code = "AGENT_ERROR"


class AgentPlanningError(AgentError):
    """Raised when an agent cannot create a valid plan."""

    error_code = "AGENT_PLANNING_ERROR"


class AgentExecutionError(AgentError):
    """Raised when an agent fails during execution."""

    error_code = "AGENT_EXECUTION_ERROR"


class AgentIterationLimitError(AgentError):
    """Raised when an agent exceeds its allowed iterations."""

    error_code = "AGENT_ITERATION_LIMIT"


class ToolError(CommandCenterError):
    """Base exception for tool-related failures."""

    error_code = "TOOL_ERROR"


class ToolNotFoundError(ToolError):
    """Raised when a requested tool does not exist."""

    error_code = "TOOL_NOT_FOUND"


class ToolPermissionError(ToolError):
    """Raised when a tool cannot be used by the current actor."""

    error_code = "TOOL_PERMISSION_DENIED"


class ToolExecutionError(ToolError):
    """Raised when a tool fails during execution."""

    error_code = "TOOL_EXECUTION_ERROR"


class ToolTimeoutError(ToolError):
    """Raised when a tool exceeds its execution timeout."""

    error_code = "TOOL_TIMEOUT"


class MCPError(CommandCenterError):
    """Base exception for MCP failures."""

    error_code = "MCP_ERROR"


class MCPConnectionError(MCPError):
    """Raised when an MCP connection cannot be established."""

    error_code = "MCP_CONNECTION_ERROR"


class MCPProtocolError(MCPError):
    """Raised when an MCP protocol operation fails."""

    error_code = "MCP_PROTOCOL_ERROR"


class RAGError(CommandCenterError):
    """Base exception for RAG-related failures."""

    error_code = "RAG_ERROR"


class DocumentProcessingError(RAGError):
    """Raised when a document cannot be processed."""

    error_code = "DOCUMENT_PROCESSING_ERROR"


class RetrievalError(RAGError):
    """Raised when knowledge retrieval fails."""

    error_code = "RETRIEVAL_ERROR"


class MemorySystemError(CommandCenterError):
    """
    Base exception for memory-related failures.

    Named ``MemorySystemError`` (not ``MemoryError``) to avoid
    shadowing the built-in ``MemoryError``, which signals an actual
    out-of-memory condition. Code that writes ``except MemoryError``
    expecting the built-in must keep working correctly.
    """

    error_code = "MEMORY_ERROR"


class ExecutionError(CommandCenterError):
    """Base exception for execution-engine failures."""

    error_code = "EXECUTION_ERROR"


class ExecutionTimeoutError(ExecutionError):
    """Raised when an execution exceeds its timeout."""

    error_code = "EXECUTION_TIMEOUT"


class ExecutionCancelledError(ExecutionError):
    """Raised when an execution is cancelled."""

    error_code = "EXECUTION_CANCELLED"


class RecoveryError(ExecutionError):
    """Raised when execution recovery fails."""

    error_code = "RECOVERY_ERROR"


class SelfCorrectionError(AgentError):
    """Raised when an agent cannot recover from a failure."""

    error_code = "SELF_CORRECTION_ERROR"