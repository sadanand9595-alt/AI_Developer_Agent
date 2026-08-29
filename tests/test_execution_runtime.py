from core.execution_runtime import ExecutionRuntime


def test_execution_runtime_full_lifecycle():
    runtime = ExecutionRuntime()

    try:
        # -------------------------------------------------
        # START
        # -------------------------------------------------

        record = runtime.start(
            "execution-001",
            task_id="task-001",
            total_steps=3,
            metadata={
                "source": "pytest",
            },
        )

        assert record.execution_id == "execution-001"
        assert record.status == "running"
        assert runtime.active_count() == 1

        # -------------------------------------------------
        # STEP 1
        # -------------------------------------------------

        runtime.start_step(
            "execution-001",
            "analyze",
            task_id="task-001",
        )

        progress = runtime.get_progress(
            "execution-001"
        )

        assert progress is not None
        assert progress.current_step == "analyze"

        runtime.complete_step(
            "execution-001",
            "analyze",
            task_id="task-001",
        )

        progress = runtime.get_progress(
            "execution-001"
        )

        assert progress is not None
        assert progress.completed_steps == 1
        assert progress.progress_percent == 33.33

        # -------------------------------------------------
        # STEP 2
        # -------------------------------------------------

        runtime.start_step(
            "execution-001",
            "generate",
            task_id="task-001",
        )

        runtime.complete_step(
            "execution-001",
            "generate",
            task_id="task-001",
        )

        progress = runtime.get_progress(
            "execution-001"
        )

        assert progress is not None
        assert progress.completed_steps == 2
        assert progress.progress_percent == 66.67

        # -------------------------------------------------
        # STEP 3
        # -------------------------------------------------

        runtime.start_step(
            "execution-001",
            "test",
            task_id="task-001",
        )

        runtime.complete_step(
            "execution-001",
            "test",
            task_id="task-001",
        )

        progress = runtime.get_progress(
            "execution-001"
        )

        assert progress is not None
        assert progress.progress_percent == 100.0
        assert progress.status == "completed"

        # -------------------------------------------------
        # MANAGER COMPLETION
        # -------------------------------------------------

        completed_record = runtime.get(
            "execution-001"
        )

        assert completed_record is not None
        assert completed_record.status == "completed"
        assert runtime.active_count() == 0

        # -------------------------------------------------
        # OBSERVER
        # -------------------------------------------------

        observation = runtime.get_observation(
            "execution-001"
        )

        assert observation is not None
        assert observation.status == "completed"
        assert observation.progress_percent == 100.0

        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        audit_records = runtime.get_audit(
            "execution-001"
        )

        assert len(audit_records) >= 1

        audit_types = [
            record.event_type
            for record in audit_records
        ]

        assert "execution.started" in audit_types
        assert "execution.step_started" in audit_types
        assert "execution.step_completed" in audit_types
        assert "execution.completed" in audit_types

        # -------------------------------------------------
        # FAILURE EXECUTION
        # -------------------------------------------------

        runtime.start(
            "execution-002",
            task_id="task-002",
            total_steps=2,
        )

        runtime.start_step(
            "execution-002",
            "generate_code",
            task_id="task-002",
        )

        failed_record = runtime.fail(
            "execution-002",
            error_code="CODE_GENERATION_FAILED",
            error_message="Test failure.",
            step_name="generate_code",
        )

        assert failed_record.status == "failed"

        failed_observation = runtime.get_observation(
            "execution-002"
        )

        assert failed_observation is not None
        assert failed_observation.status == "failed"

        failed_audit = runtime.get_audit(
            "execution-002"
        )

        failed_types = [
            record.event_type
            for record in failed_audit
        ]

        assert "execution.failed" in failed_types

        # -------------------------------------------------
        # CANCEL EXECUTION
        # -------------------------------------------------

        runtime.start(
            "execution-003",
            task_id="task-003",
            total_steps=1,
        )

        cancelled_record = runtime.cancel(
            "execution-003"
        )

        assert cancelled_record.status == "cancelled"

        cancelled_observation = (
            runtime.get_observation(
                "execution-003"
            )
        )

        assert cancelled_observation is not None
        assert cancelled_observation.status == "cancelled"

        cancelled_audit = runtime.get_audit(
            "execution-003"
        )

        cancelled_types = [
            record.event_type
            for record in cancelled_audit
        ]

        assert "execution.cancelled" in cancelled_types

        # -------------------------------------------------
        # AUDIT COUNT
        # -------------------------------------------------

        assert runtime.audit_count() > 0

    finally:
        # -------------------------------------------------
        # CLOSE
        # -------------------------------------------------

        runtime.close()