from uuid import uuid4

from core.pipeline_context import PipelineContext
from core.result import Result
from database.session import session_scope
from services.agent_orchestration_service import (
    AgentOrchestrationService,
    SpecialistSpec,
)
from services.user_service import UserService
from services.task_service import TaskService


class FakeAgentAIExecutionService:
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
        user_service = UserService(session)

        user = user_service.create_user(
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

        assert (
            first_call["context"].output_data
            in second_call["request"]
        )
def test_sequential_orchestration_continues_after_specialist_failure():
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
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
        user_service = UserService(session)

        user = user_service.create_user(
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
        assert (
            fake_agent_service.calls[0]["agent_id"]
            == "specialist-1"
        )
        assert (
            fake_agent_service.calls[1]["agent_id"]
            == "specialist-2"
        )

def test_sequential_orchestration_persists_parent_task_completion():
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
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
        task_id = data["task_id"]

        task_service = TaskService(session)
        task = task_service.get_task(task_id)

        assert task is not None
        assert task.status == "completed"
        assert task.result_json is not None
        assert task.result_json["status"] == "completed"
        assert task.result_json["final_output"] is not None
