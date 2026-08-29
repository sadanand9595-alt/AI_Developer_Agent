from core.action_registry import ActionRegistry
from core.execution_engine import ExecutionEngine
from core.pipeline_context import PipelineContext
from core.result import Result


def test_execution_engine_multi_step_success():
    registry = ActionRegistry()

    def prepare(context: PipelineContext) -> Result:
        context.set_metadata(
            "prepared",
            True,
        )

        return Result.ok(
            {
                "step": "prepared",
            }
        )

    def execute(context: PipelineContext) -> Result:
        assert context.metadata.get(
            "prepared"
        ) is True

        return Result.ok(
            {
                "step": "executed",
            }
        )

    def validate(context: PipelineContext) -> Result:
        assert context.metadata.get(
            "prepared"
        ) is True

        return Result.ok(
            {
                "step": "validated",
            }
        )

    # ---------------------------------------------------------
    # REGISTER ACTIONS
    # ---------------------------------------------------------

    assert registry.register(
        "prepare",
        prepare,
    ).is_success()

    assert registry.register(
        "execute",
        execute,
    ).is_success()

    assert registry.register(
        "validate",
        validate,
    ).is_success()

    # ---------------------------------------------------------
    # CREATE ENGINE
    # ---------------------------------------------------------

    engine = ExecutionEngine(
        registry
    )

    # ---------------------------------------------------------
    # CREATE CONTEXT
    # ---------------------------------------------------------

    context = PipelineContext(
        execution_id="engine-e2e-success",
        task_id="engine-test-task",
    )

    # ---------------------------------------------------------
    # EXECUTE PLAN
    # ---------------------------------------------------------

    result = engine.execute(
        request="Execute a multi-step test.",
        steps=[
            {
                "name": "prepare_step",
                "description": "Prepare execution.",
                "action": "prepare",
            },
            {
                "name": "execute_step",
                "description": "Execute work.",
                "action": "execute",
            },
            {
                "name": "validate_step",
                "description": "Validate result.",
                "action": "validate",
            },
        ],
        context=context,
    )

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    assert result.is_success()

    final_context = result.require_data()

    assert final_context is context

    # ---------------------------------------------------------
    # EXECUTION METADATA
    # ---------------------------------------------------------

    assert final_context.metadata[
        "plan_id"
    ]

    assert final_context.metadata[
        "step_count"
    ] == 3

    assert final_context.metadata[
        "execution_status"
    ] == "completed"

    assert final_context.metadata[
        "prepared"
    ] is True

    # ---------------------------------------------------------
    # FINAL OUTPUT
    # ---------------------------------------------------------

    assert final_context.output_data == {
        "step": "validated",
    }

    # ---------------------------------------------------------
    # STAGE RESULTS
    # ---------------------------------------------------------

    assert set(
        final_context.stage_results
    ) == {
        "prepare_step",
        "execute_step",
        "validate_step",
    }

    assert final_context.stage_results[
        "prepare_step"
    ] == {
        "step": "prepared",
    }

    assert final_context.stage_results[
        "execute_step"
    ] == {
        "step": "executed",
    }

    assert final_context.stage_results[
        "validate_step"
    ] == {
        "step": "validated",
    }

    # ---------------------------------------------------------
    # EXECUTION REGISTRY
    # ---------------------------------------------------------

    execution_id = (
        context.execution_id
    )

    assert not engine.coordinator.is_registered(
        execution_id
    )

    assert (
        engine.coordinator.active_count()
        == 0
    )

    # ---------------------------------------------------------
    # AUDIT
    # ---------------------------------------------------------

    audit = (
        engine.coordinator.get_audit(
            execution_id
        )
    )

    assert audit

    audit_types = {
        event.event_type
        for event in audit
    }

    assert (
        "execution.started"
        in audit_types
    )

    assert (
        "execution.step_started"
        in audit_types
    )

    assert (
        "execution.step_completed"
        in audit_types
    )

    assert (
        "execution.completed"
        in audit_types
    )

    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------

    engine.coordinator.close()


def test_execution_engine_action_failure_propagates():
    registry = ActionRegistry()

    # ---------------------------------------------------------
    # SUCCESSFUL ACTION
    # ---------------------------------------------------------

    def successful_action(
        context: PipelineContext,
    ) -> Result:
        return Result.ok(
            {
                "step": "success",
            }
        )

    # ---------------------------------------------------------
    # FAILING ACTION
    # ---------------------------------------------------------

    def failing_action(
        context: PipelineContext,
    ) -> Result:
        return Result.fail(
            "TEST_ACTION_FAILURE",
            "Intentional action failure.",
            details={
                "source": "engine-e2e-test",
            },
        )

    # ---------------------------------------------------------
    # ACTION THAT MUST NOT EXECUTE
    # ---------------------------------------------------------

    def should_not_execute(
        context: PipelineContext,
    ) -> Result:
        raise AssertionError(
            "Steps after a failed action "
            "must not execute."
        )

    # ---------------------------------------------------------
    # REGISTER ACTIONS
    # ---------------------------------------------------------

    assert registry.register(
        "successful_action",
        successful_action,
    ).is_success()

    assert registry.register(
        "failing_action",
        failing_action,
    ).is_success()

    assert registry.register(
        "should_not_execute",
        should_not_execute,
    ).is_success()

    # ---------------------------------------------------------
    # CREATE ENGINE
    # ---------------------------------------------------------

    engine = ExecutionEngine(
        registry
    )

    # ---------------------------------------------------------
    # CREATE CONTEXT
    # ---------------------------------------------------------

    context = PipelineContext(
        execution_id="engine-e2e-failure",
        task_id="engine-test-task",
    )

    # ---------------------------------------------------------
    # EXECUTE PLAN
    # ---------------------------------------------------------

    result = engine.execute(
        request="Execute failure test.",
        steps=[
            {
                "name": "success_step",
                "description": "Successful step.",
                "action": "successful_action",
            },
            {
                "name": "failure_step",
                "description": "Intentional failure.",
                "action": "failing_action",
            },
            {
                "name": "blocked_step",
                "description": "Must not execute.",
                "action": "should_not_execute",
            },
        ],
        context=context,
    )

    # ---------------------------------------------------------
    # RESULT MUST FAIL
    # ---------------------------------------------------------

    assert result.is_failure()

    assert result.error.code == (
        "TEST_ACTION_FAILURE"
    )

    # ---------------------------------------------------------
    # FAILURE DETAILS
    # ---------------------------------------------------------

    assert result.error.details[
        "failed_step"
    ] == "failure_step"

    assert result.error.details[
        "step_name"
    ] == "failure_step"

    assert result.error.details[
        "action"
    ] == "failing_action"

    # ---------------------------------------------------------
    # CONTEXT STATUS
    # ---------------------------------------------------------

    assert context.metadata[
        "execution_status"
    ] == "failed"

    # ---------------------------------------------------------
    # SUCCESSFUL STEP RESULT
    # ---------------------------------------------------------

    assert context.stage_results[
        "success_step"
    ] == {
        "step": "success",
    }

    # ---------------------------------------------------------
    # FAILED STEP RESULT
    # ---------------------------------------------------------

    assert context.stage_results[
        "failure_step"
    ] == {
        "error": "Intentional action failure.",
    }

    # ---------------------------------------------------------
    # NEXT STEP MUST NOT EXECUTE
    # ---------------------------------------------------------

    assert (
        "blocked_step"
        not in context.stage_results
    )

    # ---------------------------------------------------------
    # EXECUTION REGISTRY CLEANUP
    # ---------------------------------------------------------

    execution_id = (
        context.execution_id
    )

    assert not engine.coordinator.is_registered(
        execution_id
    )

    assert (
        engine.coordinator.active_count()
        == 0
    )

    # ---------------------------------------------------------
    # AUDIT
    # ---------------------------------------------------------

    audit = (
        engine.coordinator.get_audit(
            execution_id
        )
    )

    assert audit

    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------

    engine.coordinator.close()