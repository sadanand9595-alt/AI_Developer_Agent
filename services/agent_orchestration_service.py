"""
Sequential multi-agent orchestration service.

Phase 8.1:
- One durable parent Task.
- Sequential specialist execution.
- Previous successful output is passed forward.
- Specialist failures do not stop the sequence.
- Checkpoints are persisted on the parent Task.
- No child Tasks are created.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from core.pipeline_context import PipelineContext
from core.result import Result
from services.agent_ai_execution_service import AgentAIExecutionService
from services.task_service import TaskService


@dataclass(frozen=True, slots=True)
class SpecialistSpec:
    """Definition of one specialist in a sequential chain."""

    agent_id: str
    name: str | None = None


class AgentOrchestrationService:
    """Coordinate sequential specialist Agent execution."""

    def __init__(
        self,
        session: Session,
        agent_ai_service: AgentAIExecutionService,
    ) -> None:
        self._task_service = TaskService(session)
        self._agent_ai_service = agent_ai_service

    def execute_sequential(
        self,
        *,
        user_id: str,
        request: str,
        specialists: list[SpecialistSpec],
        title: str = "Sequential Agent Orchestration",
    ) -> Result[dict[str, Any]]:
        """Execute specialists sequentially under one durable parent Task."""

        if not isinstance(user_id, str) or not user_id.strip():
            return Result.fail(
                "INVALID_USER_ID",
                "User ID is required.",
            )

        if not isinstance(request, str) or not request.strip():
            return Result.fail(
                "INVALID_ORCHESTRATION_REQUEST",
                "Orchestration request is required.",
            )

        if not isinstance(specialists, list) or not specialists:
            return Result.fail(
                "INVALID_SPECIALISTS",
                "At least one specialist is required.",
            )

        normalized_specialists: list[SpecialistSpec] = []

        for specialist in specialists:
            if not isinstance(specialist, SpecialistSpec):
                return Result.fail(
                    "INVALID_SPECIALIST",
                    "Each specialist must be a SpecialistSpec.",
                )

            agent_id = specialist.agent_id.strip()

            if not agent_id:
                return Result.fail(
                    "INVALID_SPECIALIST_AGENT_ID",
                    "Specialist agent_id cannot be empty.",
                )

            normalized_specialists.append(
                SpecialistSpec(
                    agent_id=agent_id,
                    name=(
                        specialist.name.strip()
                        if isinstance(specialist.name, str)
                        and specialist.name.strip()
                        else None
                    ),
                )
            )

        parent_task = self._task_service.create_task(
            user_id=user_id.strip(),
            title=title.strip() or "Sequential Agent Orchestration",
            description=request.strip(),
            agent_id=None,
        )


        parent_execution_id = str(uuid4())

        try:
            parent_task = self._task_service.start_task(
                parent_task.id,
                execution_id=parent_execution_id,
                lease_owner_id=parent_execution_id,
            )
        except Exception as exc:
            return Result.fail(
                "ORCHESTRATION_START_FAILED",
                str(exc),
                details={
                    "task_id": parent_task.id,
                },
            )

        checkpoint: dict[str, Any] = {
            "version": 1,
            "type": "sequential_agent_orchestration",
            "task_id": parent_task.id,
            "execution_id": parent_execution_id,
            "request": request.strip(),
            "status": "running",
            "specialists": [],
        }

        try:
            self._task_service.save_orchestration_checkpoint(
                parent_task.id,
                checkpoint,
                execution_id=parent_execution_id,
                lease_owner_id=parent_execution_id,
            )
        except Exception as exc:
            return Result.fail(
                "ORCHESTRATION_CHECKPOINT_FAILED",
                str(exc),
                details={
                    "task_id": parent_task.id,
                    "execution_id": parent_execution_id,
                },
            )


        previous_output: Any = None
        successful_count = 0
        failed_count = 0

        for index, specialist in enumerate(
            normalized_specialists,
            start=1,
        ):
            specialist_execution_id = str(uuid4())

            specialist_request = request.strip()

            if previous_output is not None:
                specialist_request = (
                    f"{specialist_request}\n\n"
                    "Previous specialist output:\n"
                    f"{previous_output}"
                )

            specialist_context = PipelineContext(
                execution_id=specialist_execution_id,
                task_id=parent_task.id,
                user_id=user_id.strip(),
                agent_id=specialist.agent_id,
            )

            specialist_record: dict[str, Any] = {
                "sequence": index,
                "agent_id": specialist.agent_id,
                "name": specialist.name,
                "execution_id": specialist_execution_id,
                "status": "running",
            }

            try:
                specialist_result = self._agent_ai_service.execute(
                    agent_id=specialist.agent_id,
                    request=specialist_request,
                    context=specialist_context,
                )

                if specialist_result.is_success():
                    result_context = specialist_result.require_data()

                    output = result_context.output_data

                    specialist_record.update(
                        {
                            "status": "completed",
                            "output": output,
                            "metadata": dict(
                                result_context.metadata
                            ),
                            "stage_results": dict(
                                result_context.stage_results
                            ),
                        }
                    )

                    previous_output = output
                    successful_count += 1

                else:
                    error = specialist_result.error

                    specialist_record.update(
                        {
                            "status": "failed",
                            "error": {
                                "code": (
                                    error.code
                                    if error is not None
                                    else "SPECIALIST_FAILED"
                                ),
                                "message": (
                                    error.message
                                    if error is not None
                                    else "Specialist execution failed."
                                ),
                                "details": (
                                    dict(error.details)
                                    if error is not None
                                    else {}
                                ),
                            },
                        }
                    )

                    failed_count += 1

            except Exception as exc:
                specialist_record.update(
                    {
                        "status": "failed",
                        "error": {
                            "code": "SPECIALIST_EXECUTION_EXCEPTION",
                            "message": str(exc),
                            "details": {},
                        },
                    }
                )

                failed_count += 1

            checkpoint["specialists"].append(
                specialist_record
            )

            checkpoint["successful_count"] = (
                successful_count
            )

            checkpoint["failed_count"] = (
                failed_count
            )

            checkpoint["completed_count"] = (
                successful_count + failed_count
            )

            try:
                self._task_service.save_orchestration_checkpoint(
                    parent_task.id,
                    checkpoint,
                    execution_id=parent_execution_id,
                    lease_owner_id=parent_execution_id,
                )
            except Exception as exc:
                return Result.fail(
                    "ORCHESTRATION_CHECKPOINT_FAILED",
                    str(exc),
                    details={
                        "task_id": parent_task.id,
                        "execution_id": parent_execution_id,
                        "sequence": index,
                    },
                )

        partial_result = failed_count > 0 and successful_count > 0

        checkpoint["status"] = (
            "completed"
            if successful_count > 0
            else "failed"
        )

        checkpoint["partial_result"] = partial_result
        if successful_count == 0:
            checkpoint["error"] = {
                "code": "ALL_SPECIALISTS_FAILED",
                "message": "All specialist executions failed.",
                "specialist_errors": [
                    specialist.get("error", {})
                    for specialist in checkpoint["specialists"]
                    if specialist.get("status") == "failed"
                ],
            }

        try:
            self._task_service.save_orchestration_checkpoint(
                parent_task.id,
                checkpoint,
                execution_id=parent_execution_id,
                lease_owner_id=parent_execution_id,
            )
        except Exception as exc:
            return Result.fail(
                "ORCHESTRATION_CHECKPOINT_FAILED",
                str(exc),
                details={
                    "task_id": parent_task.id,
                    "execution_id": parent_execution_id,
                    "phase": "final_checkpoint",
                },
            )

        final_result: dict[str, Any] = {
            "type": "sequential_agent_orchestration",
            "task_id": parent_task.id,
            "execution_id": parent_execution_id,
            "status": checkpoint["status"],
            "partial_result": partial_result,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "specialists": checkpoint["specialists"],
        }

        if successful_count > 0:
            final_result["final_output"] = previous_output

            try:
                parent_task = self._task_service.complete_task(
                    parent_task.id,
                    final_result,
                    execution_id=parent_execution_id,
                    lease_owner_id=parent_execution_id,
                )
            except Exception as exc:
                return Result.fail(
                    "ORCHESTRATION_COMPLETION_FAILED",
                    str(exc),
                    details={
                        "task_id": parent_task.id,
                        "execution_id": parent_execution_id,
                    },
                )

        else:
            failure_summary = {
                "code": "ALL_SPECIALISTS_FAILED",
                "message": (
                    "All specialist executions failed."
                ),
                "specialist_errors": [
                    specialist.get("error", {})
                    for specialist in checkpoint["specialists"]
                    if specialist.get("status") == "failed"
                ],
            }

            checkpoint["error"] = failure_summary

            try:
                parent_task = self._task_service.fail_task(
                    parent_task.id,
                    failure_summary,
                    execution_id=parent_execution_id,
                    lease_owner_id=parent_execution_id,
                )
            except Exception as exc:
                return Result.fail(
                    "ORCHESTRATION_FAILURE_TRANSITION_FAILED",
                    str(exc),
                    details={
                        "task_id": parent_task.id,
                        "execution_id": parent_execution_id,
                    },
                )

            final_result["error"] = failure_summary

        return Result.ok(final_result)
