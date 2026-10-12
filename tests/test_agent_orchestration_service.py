from uuid import uuid4

from core.pipeline_context import PipelineContext
from core.result import Result
from database.session import session_scope
from services.agent_orchestration_service import (
    AgentOrchestrationService,
    SpecialistSpec,
)
from services.task_service import TaskService
from services.user_service import UserService


class FakeAgentAIExecutionService:
    """Successful fake AI execution service for orchestration tests."""

    def __init__(self):
        self.calls = []

    def execute(
        self,
        *,
        agent_id,
        request,
        context,
    ):
        self.calls.append(
            {
                "agent_id": agent_id,
                "request": request,
                "context": context,
            }
        )

        output = f"{agent_id} processed: {request}"
        context.output_data = output

        return Result.ok(context)


def test_sequential_orchestration_passes_previous_output_forward():
    with session_scope() as session:
        user = UserService(session).create_user(
            email=f"orchestration-{uuid4()}@example.com",
            name="Orchestration Test User",
            password_hash="test-hash-not-used",
        )

        fake_agent_service = FakeAgentAIExecutionService()
        service = AgentOrchestrationService(
            session=session,
            agent_ai_service=fake_agent_service,
        )

        result = service.execute_sequential(
            user_id=user.id,
            request="Start the workflow",
            specialists=[
                SpecialistSpec(
                    agent_id="specialist-1",
                    name="First Specialist",
                ),
                SpecialistSpec(
                    agent_id="specialist-2",
                    name="Second Specialist",
                ),
            ],
        )

        assert result.is_success()

        data = result.require_data()

        assert data["status"] == "completed"
        assert data["successful_count"] == 2
        assert data["failed_count"] == 0
        assert data["partial_result"] is False

        assert len(fake_agent_service.calls) == 2

        first_call = fake_agent_service.calls[0]
        second_call = fake_agent_service.calls[1]

        assert first_call["agent_id"] == "specialist-1"
        assert first_call["request"] == "Start the workflow"

        assert second_call["agent_id"] == "specialist-2"
        assert "Previous specialist output:" in second_call["request"]

        assert first_call["context"].output_data in second_call["request"]


def test_sequential_orchestration_continues_after_specialist_failure():
    with session_scope() as session:
        user = UserService(session).create_user(
            email=f"orchestration-failure-{uuid4()}@example.com",
            name="Orchestration Failure Test User",
            password_hash="test-hash-not-used",
        )

        class FailureAwareFakeAgentService:
            def __init__(self):
                self.calls = []

            def execute(
                self,
                *,
                agent_id,
                request,
                context,
            ):
                self.calls.append(
                    {
                        "agent_id": agent_id,
                        "request": request,
                        "context": context,
                    }
                )

                if agent_id == "specialist-2":
                    return Result.fail(
                        "SPECIALIST_FAILURE",
                        "Expected specialist failure.",
                    )

                output = f"{agent_id} completed"
                context.output_data = output

                return Result.ok(context)

        fake_agent_service = FailureAwareFakeAgentService()
        service = AgentOrchestrationService(
            session=session,
            agent_ai_service=fake_agent_service,
        )

        result = service.execute_sequential(
            user_id=user.id,
            request="Run the workflow",
            specialists=[
                SpecialistSpec(
                    agent_id="specialist-1",
                    name="First Specialist",
                ),
                SpecialistSpec(
                    agent_id="specialist-2",
                    name="Failing Specialist",
                ),
                SpecialistSpec(
                    agent_id="specialist-3",
                    name="Third Specialist",
                ),
            ],
        )

        assert result.is_success()

        data = result.require_data()

        assert data["status"] == "completed"
        assert data["partial_result"] is True
        assert data["successful_count"] == 2
        assert data["failed_count"] == 1

        assert len(fake_agent_service.calls) == 3

        assert fake_agent_service.calls[0]["agent_id"] == "specialist-1"
        assert fake_agent_service.calls[1]["agent_id"] == "specialist-2"
        assert fake_agent_service.calls[2]["agent_id"] == "specialist-3"

        assert (
            "specialist-1 completed"
            in fake_agent_service.calls[1]["request"]
        )

        assert (
            "specialist-1 completed"
            in fake_agent_service.calls[2]["request"]
        )


def test_sequential_orchestration_fails_when_all_specialists_fail():
    with session_scope() as session:
        user = UserService(session).create_user(
            email=f"orchestration-all-fail-{uuid4()}@example.com",
            name="Orchestration All Failure Test User",
            password_hash="test-hash-not-used",
        )

        class AlwaysFailFakeAgentService:
            def __init__(self):
                self.calls = []

            def execute(
                self,
                *,
                agent_id,
                request,
                context,
            ):
                self.calls.append(
                    {
                        "agent_id": agent_id,
                        "request": request,
                    }
                )

                return Result.fail(
                    "SPECIALIST_FAILURE",
                    f"{agent_id} failed as expected.",
                )

        fake_agent_service = AlwaysFailFakeAgentService()
        service = AgentOrchestrationService(
            session=session,
            agent_ai_service=fake_agent_service,
        )

        result = service.execute_sequential(
            user_id=user.id,
            request="Run the failure workflow",
            specialists=[
                SpecialistSpec(
                    agent_id="specialist-1",
                    name="First Failing Specialist",
                ),
                SpecialistSpec(
                    agent_id="specialist-2",
                    name="Second Failing Specialist",
                ),
            ],
        )

        assert result.is_success()

        data = result.require_data()

        assert data["status"] == "failed"
        assert data["partial_result"] is False
        assert data["successful_count"] == 0
        assert data["failed_count"] == 2

        assert "error" in data
        assert data["error"]["code"] == "ALL_SPECIALISTS_FAILED"

        assert len(fake_agent_service.calls) == 2
        assert fake_agent_service.calls[0]["agent_id"] == "specialist-1"
        assert fake_agent_service.calls[1]["agent_id"] == "specialist-2"


def test_sequential_orchestration_persists_parent_task_completion():
    with session_scope() as session:
        user = UserService(session).create_user(
            email=f"orchestration-task-{uuid4()}@example.com",
            name="Orchestration Task Test User",
            password_hash="test-hash-not-used",
        )

        fake_agent_service = FakeAgentAIExecutionService()
        service = AgentOrchestrationService(
            session=session,
            agent_ai_service=fake_agent_service,
        )

        result = service.execute_sequential(
            user_id=user.id,
            request="Persist the workflow result",
            specialists=[
                SpecialistSpec(
                    agent_id="specialist-1",
                    name="First Specialist",
                ),
            ],
        )

        assert result.is_success()

        data = result.require_data()
        task = TaskService(session).get_task(data["task_id"])

        assert task is not None
        assert task.status == "completed"
        assert task.result_json is not None
        assert task.result_json["status"] == "completed"
        assert task.result_json["final_output"] is not None


def test_sequential_orchestration_persists_final_checkpoint_status():
    with session_scope() as session:
        user = UserService(session).create_user(
            email=f"orchestration-checkpoint-{uuid4()}@example.com",
            name="Orchestration Checkpoint Test User",
            password_hash="test-hash-not-used",
        )

        service = AgentOrchestrationService(
            session=session,
            agent_ai_service=FakeAgentAIExecutionService(),
        )

        result = service.execute_sequential(
            user_id=user.id,
            request="Verify final checkpoint persistence",
            specialists=[
                SpecialistSpec(
                    agent_id="checkpoint-specialist",
                    name="Checkpoint Specialist",
                ),
            ],
        )

        assert result.is_success()

        data = result.require_data()
        task = TaskService(session).get_task(data["task_id"])

        assert task is not None
        assert task.status == "completed"
        assert task.plan_json is not None
        assert task.plan_json["status"] == "completed"
        assert task.plan_json["partial_result"] is False
        assert task.plan_json["successful_count"] == 1
        assert task.plan_json["failed_count"] == 0


def test_sequential_orchestration_persists_failed_checkpoint_status():
    with session_scope() as session:
        user = UserService(session).create_user(
            email=f"orchestration-failed-checkpoint-{uuid4()}@example.com",
            name="Failed Checkpoint Test User",
            password_hash="test-hash-not-used",
        )

        class AlwaysFailFakeAgentService:
            def execute(
                self,
                *,
                agent_id,
                request,
                context,
            ):
                return Result.fail(
                    "SPECIALIST_FAILURE",
                    f"{agent_id} failed as expected.",
                )

        service = AgentOrchestrationService(
            session=session,
            agent_ai_service=AlwaysFailFakeAgentService(),
        )

        result = service.execute_sequential(
            user_id=user.id,
            request="Verify failed checkpoint persistence",
            specialists=[
                SpecialistSpec(
                    agent_id="failing-specialist",
                    name="Failing Specialist",
                ),
            ],
        )

        assert result.is_success()

        data = result.require_data()
        task = TaskService(session).get_task(data["task_id"])

        assert task is not None
        assert task.status == "failed"
        assert task.plan_json is not None
        assert task.plan_json["status"] == "failed"
        assert task.plan_json["successful_count"] == 0
        assert task.plan_json["failed_count"] == 1
        assert task.plan_json["error"]["code"] == "ALL_SPECIALISTS_FAILED"
