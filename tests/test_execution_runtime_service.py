import pytest

from core.execution_runtime import ExecutionRuntime
from core.execution_runtime_service import ExecutionRuntimeService


def test_execution_runtime_service_full_lifecycle():
    runtime = ExecutionRuntime()
    service = ExecutionRuntimeService(runtime)

    try:
        # -------------------------------------------------
        # START
        # -------------------------------------------------

        record = service.start(
            execution_id="execution-service-001",
            task_id="task-service-001",
            total_steps=2,
            metadata={
                "source": "pytest",
            },
        )

        assert record.execution_id == (
            "execution-service-001"
        )
        assert record.status == "running"
        assert service.active_count() == 1

        # -------------------------------------------------
        # STEP 1
        # -------------------------------------------------

        service.start_step(
            execution_id="execution-service-001",
            step_name="analyze",
            task_id="task-service-001",
        )

        progress = service.get_progress(
            "execution-service-001"
        )

        assert progress is not None
        assert progress.current_step == "analyze"

        service.complete_step(
            execution_id="execution-service-001",
            step_name="analyze",
            task_id="task-service-001",
        )

        progress = service.get_progress(
            "execution-service-001"
        )

        assert progress is not None
        assert progress.completed_steps == 1
        assert progress.progress_percent == 50.0

        # -------------------------------------------------
        # STEP 2
        # -------------------------------------------------

        service.start_step(
            execution_id="execution-service-001",
            step_name="generate",
            task_id="task-service-001",
        )

        service.complete_step(
            execution_id="execution-service-001",
            step_name="generate",
            task_id="task-service-001",
        )

        progress = service.get_progress(
            "execution-service-001"
        )

        assert progress is not None
        assert progress.progress_percent == 100.0
        assert progress.status == "completed"

        # -------------------------------------------------
        # EXECUTION STATE
        # -------------------------------------------------

        completed = service.get(
            "execution-service-001"
        )

        assert completed is not None
        assert completed.status == "completed"

        # -------------------------------------------------
        # OBSERVATION
        # -------------------------------------------------

        observation = service.get_observation(
            "execution-service-001"
        )

        assert observation is not None
        assert observation.status == "completed"
        assert observation.progress_percent == 100.0

        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        audit = service.get_audit(
            "execution-service-001"
        )

        assert len(audit) > 0

        audit_types = [
            item.event_type
            for item in audit
        ]

        assert "execution.started" in audit_types
        assert "execution.step_started" in audit_types
        assert "execution.step_completed" in audit_types
        assert "execution.completed" in audit_types

        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        service.start(
            execution_id="execution-service-002",
            task_id="task-service-002",
            total_steps=1,
        )

        service.start_step(
            execution_id="execution-service-002",
            step_name="generate_code",
            task_id="task-service-002",
        )

        failed = service.fail(
            execution_id="execution-service-002",
            error_code="GENERATION_FAILED",
            error_message="Generation test failed.",
            step_name="generate_code",
        )

        assert failed.status == "failed"

        failure_audit = service.get_audit(
            "execution-service-002"
        )

        assert any(
            item.event_type == "execution.failed"
            for item in failure_audit
        )

        # -------------------------------------------------
        # CANCEL
        # -------------------------------------------------

        service.start(
            execution_id="execution-service-003",
            task_id="task-service-003",
            total_steps=1,
        )

        cancelled = service.cancel(
            execution_id="execution-service-003"
        )

        assert cancelled.status == "cancelled"

        cancel_audit = service.get_audit(
            "execution-service-003"
        )

        assert any(
            item.event_type == "execution.cancelled"
            for item in cancel_audit
        )

        # -------------------------------------------------
        # INVALID RUNTIME
        # -------------------------------------------------

        with pytest.raises(TypeError):
            ExecutionRuntimeService(
                "invalid-runtime"
            )

    finally:
        # -------------------------------------------------
        # CLOSE
        # -------------------------------------------------

        service.close()