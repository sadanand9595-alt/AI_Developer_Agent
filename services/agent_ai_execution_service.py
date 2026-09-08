"""
Agent-aware AI execution service for AI Command Center.

Bridges persistent Agent records and the existing autonomous
AI execution pipeline without putting AI-specific logic into
AgentRuntime itself.
"""

from __future__ import annotations

from core.pipeline_context import PipelineContext
from core.result import Result
from services.agent_runtime_service import AgentRuntimeService
from services.ai_execution_service import AIExecutionService


class AgentAIExecutionService:
    """
    Execute AI requests through registered persistent Agents.

    The persistent Agent provides configuration and execution
    limits. AgentRuntime remains responsible for lifecycle
    management, while AIExecutionService remains responsible
    for planning, execution, observation, and replanning.
    """

    def __init__(
        self,
        ai_execution_service: AIExecutionService,
        agent_runtime_service: AgentRuntimeService,
    ) -> None:
        if not isinstance(
            ai_execution_service,
            AIExecutionService,
        ):
            raise TypeError(
                "Expected an AIExecutionService instance."
            )

        if not isinstance(
            agent_runtime_service,
            AgentRuntimeService,
        ):
            raise TypeError(
                "Expected an AgentRuntimeService instance."
            )

        self._ai_execution_service = ai_execution_service
        self._agent_runtime_service = agent_runtime_service

    def execute(
        self,
        *,
        agent_id: str,
        request: str,
        context: PipelineContext | None = None,
    ) -> Result[PipelineContext]:
        """Execute a request through a registered autonomous Agent."""

        if not isinstance(agent_id, str):
            return Result.fail(
                "INVALID_AGENT_ID",
                "Agent ID must be a string.",
            )

        normalized_agent_id = agent_id.strip()

        if not normalized_agent_id:
            return Result.fail(
                "INVALID_AGENT_ID",
                "Agent ID cannot be empty.",
            )

        if not isinstance(request, str):
            return Result.fail(
                "INVALID_AI_EXECUTION_REQUEST",
                "AI execution request must be a string.",
            )

        normalized_request = request.strip()

        if not normalized_request:
            return Result.fail(
                "EMPTY_AI_EXECUTION_REQUEST",
                "AI execution request cannot be empty.",
            )

        agent_result = self._agent_runtime_service.get_agent(
            normalized_agent_id
        )

        if agent_result.is_failure():
            return Result.fail(
                agent_result.error.code,
                agent_result.error.message,
                details=agent_result.error.details,
            )

        agent = agent_result.require_data()

        if (
            not isinstance(agent.max_iterations, int)
            or isinstance(agent.max_iterations, bool)
            or agent.max_iterations < 1
        ):
            return Result.fail(
                "INVALID_AGENT_CONFIGURATION",
                "Agent max_iterations must be a positive integer.",
                details={
                    "agent_id": normalized_agent_id,
                    "max_iterations": agent.max_iterations,
                },
            )

        runtime_result = self._agent_runtime_service.get_runtime(
            normalized_agent_id
        )

        if runtime_result.is_failure():
            return Result.fail(
                runtime_result.error.code,
                runtime_result.error.message,
                details=runtime_result.error.details,
            )

        runtime = runtime_result.require_data()

        pipeline_context = context or PipelineContext()

        if not isinstance(
            pipeline_context,
            PipelineContext,
        ):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        pipeline_context.set_input(
            normalized_request
        )

        pipeline_context.set_metadata(
            "request",
            normalized_request,
        )

        pipeline_context.set_metadata(
            "agent_id",
            agent.id,
        )

        pipeline_context.set_metadata(
            "agent_type",
            agent.agent_type,
        )

        pipeline_context.set_metadata(
            "model_provider",
            agent.model_provider,
        )

        pipeline_context.set_metadata(
            "model_name",
            agent.model_name,
        )

        pipeline_context.set_metadata(
            "capabilities",
            list(agent.capabilities or []),
        )

        pipeline_context.set_metadata(
            "agent_configuration",
            dict(agent.configuration or {}),
        )

        pipeline_context.set_metadata(
            "max_iterations",
            agent.max_iterations,
        )

        pipeline_context.set_metadata(
            "agent_execution",
            True,
        )

        def _operation(_execution_context) -> Result[PipelineContext]:
            return self._ai_execution_service.execute_agent(
                normalized_request,
                context=pipeline_context,
                max_iterations=agent.max_iterations,
            )

        execution = runtime.execute(
            context=self._build_runtime_context(
                pipeline_context,
                agent.id,
            ),
            operation=_operation,
        )

        if execution.result.is_failure():
            return Result.fail(
                execution.result.error.code,
                execution.result.error.message,
                details=execution.result.error.details,
            )

        result_context = execution.result.require_data()

        result_context.set_metadata(
            "agent_runtime_status",
            execution.status.value,
        )

        result_context.set_metadata(
            "agent_id",
            agent.id,
        )

        return Result.ok(result_context)

    @staticmethod
    def _build_runtime_context(
        context: PipelineContext,
        agent_id: str,
    ):
        """
        Build the ExecutionContext required by AgentRuntime.

        The AI pipeline continues using PipelineContext; the
        runtime receives only the lifecycle/execution boundary
        context required by AgentRuntime.
        """

        from core.context import ExecutionContext

        return ExecutionContext.create(
            user_id=context.user_id,
            task_id=context.task_id,
            agent_id=agent_id,
            execution_id=context.execution_id,
            metadata={
                "ai_execution": True,
                "agent_id": agent_id,
            },
        )


__all__ = ["AgentAIExecutionService"]
