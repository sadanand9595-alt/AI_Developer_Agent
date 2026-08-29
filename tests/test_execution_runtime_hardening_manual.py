from core.execution_runtime import ExecutionRuntime


def main() -> None:
    print("=" * 60)
    print("EXECUTION RUNTIME HARDENING MANUAL TEST")
    print("=" * 60)

    runtime = ExecutionRuntime()

    try:
        # -----------------------------------------------------
        # 1. START
        # -----------------------------------------------------

        record = runtime.start(
            "hardening-001",
            task_id="hardening-task-001",
            total_steps=2,
        )

        assert record.execution_id == "hardening-001"
        assert record.status == "running"

        print("START: PASS")

        # -----------------------------------------------------
        # 2. STEP START
        # -----------------------------------------------------

        progress = runtime.start_step(
            "hardening-001",
            "step_one",
            task_id="hardening-task-001",
        )

        assert progress.current_step == "step_one"

        print("STEP START: PASS")

        # -----------------------------------------------------
        # 3. STEP COMPLETE
        # -----------------------------------------------------

        progress = runtime.complete_step(
            "hardening-001",
            "step_one",
            task_id="hardening-task-001",
        )

        assert progress.completed_steps == 1
        assert progress.progress_percent == 50.0

        print("STEP COMPLETE: PASS")

        # -----------------------------------------------------
        # 4. SECOND STEP
        # -----------------------------------------------------

        runtime.start_step(
            "hardening-001",
            "step_two",
            task_id="hardening-task-001",
        )

        progress = runtime.complete_step(
            "hardening-001",
            "step_two",
            task_id="hardening-task-001",
        )

        assert progress.completed_steps == 2
        assert progress.progress_percent == 100.0
        assert progress.status == "completed"

        print("FINAL STEP: PASS")

        # -----------------------------------------------------
        # 5. EXECUTION MUST BE INACTIVE
        # -----------------------------------------------------

        assert runtime.active_count() == 0

        completed = runtime.get(
            "hardening-001"
        )

        assert completed is not None
        assert completed.status == "completed"

        print("COMPLETION STATE: PASS")

        # -----------------------------------------------------
        # 6. OBSERVATION
        # -----------------------------------------------------

        observation = runtime.get_observation(
            "hardening-001"
        )

        assert observation is not None
        assert observation.status == "completed"
        assert observation.progress_percent == 100.0

        print("OBSERVATION: PASS")

        # -----------------------------------------------------
        # 7. AUDIT
        # -----------------------------------------------------

        audit = runtime.get_audit(
            "hardening-001"
        )

        assert audit

        audit_types = {
            item.event_type
            for item in audit
        }

        assert "execution.started" in audit_types
        assert "execution.step_started" in audit_types
        assert "execution.step_completed" in audit_types
        assert "execution.completed" in audit_types

        print("AUDIT: PASS")

        # -----------------------------------------------------
        # 8. FAILURE LIFECYCLE
        # -----------------------------------------------------

        runtime.start(
            "hardening-002",
            task_id="hardening-task-002",
            total_steps=1,
        )

        runtime.start_step(
            "hardening-002",
            "failing_step",
            task_id="hardening-task-002",
        )

        failed = runtime.fail(
            "hardening-002",
            error_code="HARDENING_TEST_FAILURE",
            error_message="Intentional hardening failure.",
            step_name="failing_step",
        )

        assert failed.status == "failed"
        assert runtime.active_count() == 0

        print("FAILURE LIFECYCLE: PASS")

        # -----------------------------------------------------
        # 9. FAILURE OBSERVATION
        # -----------------------------------------------------

        failed_observation = runtime.get_observation(
            "hardening-002"
        )

        assert failed_observation is not None
        assert failed_observation.status == "failed"

        print("FAILURE OBSERVATION: PASS")

        # -----------------------------------------------------
        # 10. FAILURE AUDIT
        # -----------------------------------------------------

        failure_audit = runtime.get_audit(
            "hardening-002"
        )

        failure_audit_types = {
            item.event_type
            for item in failure_audit
        }

        assert "execution.failed" in failure_audit_types

        print("FAILURE AUDIT: PASS")

        # -----------------------------------------------------
        # 11. CANCEL LIFECYCLE
        # -----------------------------------------------------

        runtime.start(
            "hardening-003",
            task_id="hardening-task-003",
            total_steps=1,
        )

        cancelled = runtime.cancel(
            "hardening-003"
        )

        assert cancelled.status == "cancelled"
        assert runtime.active_count() == 0

        print("CANCEL LIFECYCLE: PASS")

        # -----------------------------------------------------
        # 12. CANCEL AUDIT
        # -----------------------------------------------------

        cancel_audit = runtime.get_audit(
            "hardening-003"
        )

        cancel_audit_types = {
            item.event_type
            for item in cancel_audit
        }

        assert "execution.cancelled" in cancel_audit_types

        print("CANCEL AUDIT: PASS")

        # -----------------------------------------------------
        # FINAL
        # -----------------------------------------------------

        print()
        print("=" * 60)
        print("EXECUTION RUNTIME HARDENING: PASS")
        print("=" * 60)

    finally:
        runtime.close()


if __name__ == "__main__":
    main()