"""
Execution service for AI Command Center.

Provides the production-facing service boundary between
structured execution requests and standardized responses.
"""

from __future__ import annotations

from core.execution_engine import ExecutionEngine
from core.execution_request import ExecutionRequest
from core.execution_response import ExecutionResponse
from core.pipeline_context import PipelineContext
from core.result import Result


class ExecutionService:
    """High-level service for task execution."""

    def __init__(
        self,
        engine: ExecutionEngine,
    ) -> None:
        self._engine = engine

    def execute(
        self,
        *,
        execution_request: ExecutionRequest,
        steps: list[dict[str, object]],
    ) -> ExecutionResponse:
        """
        Execute a structured request and return a standardized
        execution response.
        """

        if not isinstance(
            execution_request,
            ExecutionRequest,
        ):
            return ExecutionResponse.failure_response(
                execution_id="unknown",
                code="INVALID_EXECUTION_REQUEST",
                message=(
                    "Expected an ExecutionRequest instance."
                ),
            )

        execution_id = self._resolve_execution_id(
            execution_request
        )

        context = PipelineContext(
            execution_id=execution_id,
            task_id=execution_request.task_id,
            user_id=execution_request.user_id,
            agent_id=execution_request.agent_id,
        )

        context.set_metadata(
            "session_id",
            execution_request.session_id,
        )

        context.set_metadata(
            "conversation_id",
            execution_request.conversation_id,
        )

        context.set_metadata(
            "workspace_root",
            execution_request.workspace_root,
        )

        context.set_metadata(
            "working_directory",
            execution_request.working_directory,
        )

        context.set_metadata(
            "permissions",
            tuple(
                sorted(
                    execution_request.permissions
                )
            ),
        )

        for key, value in execution_request.metadata.items():
            context.set_metadata(
                key,
                value,
            )

        result = self._engine.execute(
            request=execution_request.request,
            steps=steps,
            context=context,
        )

        if result.is_failure():
            return self._failure_response(
                execution_id=execution_id,
                result=result,
                context=context,
            )

        final_context = result.require_data()

        plan_id = final_context.get_metadata(
            "plan_id"
        )

        if not isinstance(plan_id, str):
            plan_id = None

        metadata = dict(
            final_context.metadata
        )

        metadata["execution_status"] = (
            final_context.get_metadata(
                "execution_status",
                "completed",
            )
        )

        return ExecutionResponse.success_response(
            execution_id=execution_id,
            plan_id=plan_id,
            output=final_context.output_data,
            metadata=metadata,
        )

    @staticmethod
    def _resolve_execution_id(
        request: ExecutionRequest,
    ) -> str:
        """
        Resolve a stable execution ID.

        The request may optionally provide one through metadata.
        Otherwise PipelineContext generates one.
        """

        candidate = request.metadata.get(
            "execution_id"
        )

        if isinstance(
            candidate,
            str,
        ) and candidate.strip():
            return candidate.strip()

        return PipelineContext(
            user_id=request.user_id,
            task_id=request.task_id,
        ).execution_id

    @staticmethod
    def _failure_response(
        *,
        execution_id: str,
        result: Result[PipelineContext],
        context: PipelineContext,
    ) -> ExecutionResponse:
        """Convert an execution Result failure into a response."""

        error = result.error

        if error is None:
            return ExecutionResponse.failure_response(
                execution_id=execution_id,
                code="EXECUTION_FAILED",
                message="Execution failed.",
                metadata=dict(
                    context.metadata
                ),
            )

        plan_id = context.get_metadata(
            "plan_id"
        )

        if not isinstance(plan_id, str):
            plan_id = None

        return ExecutionResponse.failure_response(
            execution_id=execution_id,
            plan_id=plan_id,
            code=error.code,
            message=error.message,
            details=error.details,
            metadata=dict(
                context.metadata
            ),
        )