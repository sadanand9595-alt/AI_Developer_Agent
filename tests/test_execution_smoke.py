from uuid import uuid4

from core.execution_application import ExecutionApplication


def test_execution_application_smoke():
    application = ExecutionApplication()

    execution_id = f"pytest-execution-{uuid4()}"

    try:
        system = application.start()

        assert application.is_running()
        assert system is application.system()

        record = application.start_execution(
            execution_id,
            task_id=f"pytest-task-{uuid4()}",
            total_steps=1,
            metadata={
                "source": "pytest-smoke",
            },
        )

        assert record.execution_id == execution_id
        assert record.status == "running"
        assert application.registered_count() == 1

        application.start_step(
            execution_id,
            "smoke_step",
            task_id=record.task_id,
        )

        application.complete_step(
            execution_id,
            "smoke_step",
            task_id=record.task_id,
        )

        progress = application.get_progress(
            execution_id
        )

        assert progress is not None
        assert progress.progress_percent == 100.0
        assert progress.status == "completed"

        execution = application.get(
            execution_id
        )

        assert execution is not None
        assert execution.status == "completed"

        observation = application.get_observation(
            execution_id
        )

        assert observation is not None
        assert observation.status == "completed"
        assert observation.progress_percent == 100.0

        audit = application.get_audit(
            execution_id
        )

        assert audit

        audit_types = {
            event.event_type
            for event in audit
        }

        assert "execution.started" in audit_types
        assert "execution.step_started" in audit_types
        assert "execution.step_completed" in audit_types
        assert "execution.completed" in audit_types

        assert application.registered_count() == 0
        assert application.active_count() == 0

    finally:
        application.stop()
