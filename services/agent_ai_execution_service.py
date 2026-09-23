"""
Agent-aware AI execution service.

Provides the application-level bridge between AgentRuntimeService and
the autonomous AI execution pipeline.

Responsibilities:
- Resolve and validate the requested Agent.
- Resolve the Agent runtime.
- Build and enrich the PipelineContext used by the AI pipeline.
- Build the immutable ExecutionContext required by AgentRuntime.
- Execute the AI pipeline inside the controlled AgentRuntime boundary.
- Preserve execution/task identity.
- Forward durable TaskService when available.
"""

from __future__ import annotations

from typing import Any

from core.context import ExecutionContext
from core.pipeline_context import PipelineContext
from core.result import Result
from services.agent_runtime_service import AgentRuntimeService
from services.ai_execution_service import AIExecutionService
from services.task_service import TaskService


class AgentAIExecutionService:
    """
    Execute an Agent through the controlled runtime and autonomous
    AI execution pipeline.

    AgentRuntimeService owns persistent Agent validation and runtime
    resolution.

    AgentRuntime owns lifecycle transitions and the immutable
    ExecutionContext boundary.

    AIExecutionService owns planning, iteration, approval handling,
    and autonomous execution.
    """

    def __init__(
        self,
        agent_runtime_service: AgentRuntimeService,
        ai_execution_service: AIExecutionService,
    ) -> None:
        self._agent_runtime_service = agent_runtime_service
        self._ai_execution_service = ai_execution_service

    def execute(
        self,
        *,
        agent_id: str,
        request: str,
        context: PipelineContext | None = None,
        task_service: TaskService | None = None,
    ) -> Result[PipelineContext]:
        """
        Execute an Agent request through the controlled runtime.

        Args:
            agent_id:
                Registered Agent identifier.

            request:
                Natural-language execution request.

            context:
                Optional existing PipelineContext. When supplied,
                its execution/task/user identity is preserved.

            task_service:
                Optional durable TaskService. When supplied, it is
                forwarded to AIExecutionService so approval-gated
                executions can transition their durable Task.

        Returns:
            Result containing the final PipelineContext or an error.
        """

        normalized_agent_id = self._normalize_agent_id(
            agent_id
        )

        if not normalized_agent_id:
            return Result.fail(
                "INVALID_AGENT_ID",
                "Agent ID is required.",
                details={
                    "agent_id": agent_id,
                },
            )

        if not isinstance(request, str) or not request.strip():
            return Result.fail(
                "INVALID_AGENT_REQUEST",
                "Agent execution request is required.",
                details={
                    "agent_id": normalized_agent_id,
                },
            )

        # ---------------------------------------------------------------
        # 1. Resolve persistent Agent
        # ---------------------------------------------------------------

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

        # ---------------------------------------------------------------
        # 2. Build PipelineContext for AI execution
        # ---------------------------------------------------------------

        pipeline_context = self._build_pipeline_context(
            context=context,
            agent=agent,
            request=request.strip(),
        )

        normalized_request = request.strip()

        # ---------------------------------------------------------------
        # 3. Resolve controlled AgentRuntime
        # ---------------------------------------------------------------

        runtime_result = self._agent_runtime_service.get_runtime(
            agent.id
        )

        if runtime_result.is_failure():
            return Result.fail(
                runtime_result.error.code,
                runtime_result.error.message,
                details=runtime_result.error.details,
            )

        runtime = runtime_result.require_data()

        # ---------------------------------------------------------------
        # 4. Build immutable ExecutionContext
        #
        # AgentRuntime requires ExecutionContext.
        # AIExecutionService continues to use PipelineContext.
        # ---------------------------------------------------------------

        try:
            execution_context = self._build_execution_context(
                pipeline_context=pipeline_context,
                agent_id=agent.id,
            )
        except Exception as exc:
            return Result.fail(
                "EXECUTION_CONTEXT_ERROR",
                str(exc),
                details={
                    "agent_id": agent.id,
                    "execution_id": pipeline_context.execution_id,
                    "task_id": pipeline_context.task_id,
                },
            )

        # ---------------------------------------------------------------
        # 5. AI operation executed inside AgentRuntime
        # ---------------------------------------------------------------

        def _operation(
            runtime_context: ExecutionContext,
        ) -> Result[PipelineContext]:
            """
            Execute the autonomous AI pipeline.

            AgentRuntime supplies the immutable ExecutionContext.
            The AI pipeline intentionally continues using the existing
            PipelineContext abstraction.

            The execution identity is already shared between both
            contexts, so no new execution ID is generated here.
            """

            # Keep the existing PipelineContext as the AI pipeline
            # context. The AgentRuntime ExecutionContext remains the
            # lifecycle/security boundary.
            #
            # This is important because PipelineContext is mutable and
            # carries AI pipeline output/stage metadata, while
            # ExecutionContext is intentionally immutable.
            pipeline_context.set_metadata(
                "runtime_execution_id",
                str(runtime_context.execution_id),
            )

            execute_kwargs: dict[str, Any] = {
                "context": pipeline_context,
                "max_iterations": agent.max_iterations,
            }

            # Phase 7.3 durable lifecycle bridge.
            #
            # Only pass task_service when available. This keeps existing
            # lightweight callers and test doubles compatible with the
            # pre-Phase-7.3 execute_agent() signature.
            if task_service is not None:
                execute_kwargs["task_service"] = task_service

            return self._ai_execution_service.execute_agent(
                normalized_request,
                **execute_kwargs,
            )

        # ---------------------------------------------------------------
        # 6. Execute through controlled AgentRuntime
        # ---------------------------------------------------------------

        try:
            runtime_execution = runtime.execute(
                context=execution_context,
                operation=_operation,
            )
        except Exception as exc:
            return Result.fail(
                "AGENT_EXECUTION_ERROR",
                str(exc),
                details={
                    "agent_id": agent.id,
                    "execution_id": pipeline_context.execution_id,
                    "task_id": pipeline_context.task_id,
                },
            )

        if runtime_execution is None:
            return Result.fail(
                "AGENT_EXECUTION_ERROR",
                "Agent runtime returned no execution result.",
                details={
                    "agent_id": agent.id,
                    "execution_id": pipeline_context.execution_id,
                    "task_id": pipeline_context.task_id,
                },
            )

        execution_result = runtime_execution.result

        if not isinstance(
            execution_result,
            Result,
        ):
            return Result.fail(
                "AGENT_EXECUTION_ERROR",
                "Agent runtime returned an invalid execution result.",
                details={
                    "agent_id": agent.id,
                    "execution_id": pipeline_context.execution_id,
                    "task_id": pipeline_context.task_id,
                },
            )

        return execution_result

    def _build_pipeline_context(
        self,
        *,
        context: PipelineContext | None,
        agent: Any,
        request: str,
    ) -> PipelineContext:
        """
        Build or enrich the mutable PipelineContext used by AI execution.

        Existing execution/task/user identity is preserved.
        """

        if context is None:
            pipeline_context = PipelineContext(
                user_id=None,
                agent_id=agent.id,
            )
        else:
            pipeline_context = context

            if not pipeline_context.agent_id:
                pipeline_context.agent_id = agent.id

        pipeline_context.set_input(
            request
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
            agent.capabilities,
        )

        pipeline_context.set_metadata(
            "agent_configuration",
            agent.configuration,
        )

        pipeline_context.set_metadata(
            "max_iterations",
            agent.max_iterations,
        )

        pipeline_context.set_metadata(
            "agent_execution",
            True,
        )

        return pipeline_context

    @staticmethod
    def _build_execution_context(
        *,
        pipeline_context: PipelineContext,
        agent_id: str,
    ) -> ExecutionContext:
        """
        Convert the existing PipelineContext identity into the immutable
        ExecutionContext required by AgentRuntime.

        The execution ID is preserved exactly. No new execution identity
        is generated.
        """

        if not pipeline_context.user_id:
            raise ValueError(
                "PipelineContext requires a user_id for Agent execution."
            )

        if not pipeline_context.task_id:
            raise ValueError(
                "PipelineContext requires a task_id for Agent execution."
            )

        return ExecutionContext.create(
            user_id=str(
                pipeline_context.user_id
            ),
            task_id=str(
                pipeline_context.task_id
            ),
            agent_id=agent_id,
            execution_id=str(
                pipeline_context.execution_id
            ),
            lease_owner_id=str(
                pipeline_context.execution_id
            ),
            metadata=dict(
                pipeline_context.metadata
            ),
        )

    @staticmethod
    def _normalize_agent_id(
        agent_id: str,
    ) -> str:
        """Normalize an Agent identifier before lookup."""

        if not isinstance(agent_id, str):
            return ""

        return agent_id.strip()


__all__ = ["AgentAIExecutionService"]