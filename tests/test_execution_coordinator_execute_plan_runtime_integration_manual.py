"""
Manual integration test for:

ExecutionCoordinator
    +
ExecutionEngine / PlanExecutor
    +
Runtime integration

This file is intentionally executable directly:

    python tests\test_execution_coordinator_execute_plan_runtime_integration_manual.py

It also remains compatible with pytest collection.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------
# PROJECT ROOT BOOTSTRAP
# ---------------------------------------------------------
#
# When this file is executed directly:
#
#     python tests\test_xxx.py
#
# Python puts tests\ on sys.path, not the project root.
#
# Add D:\AI_COMMAND_CENTER (project root) explicitly so:
#
#     from core....
#
# works consistently.
#

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ---------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------

from core.action_executor import (
    ActionExecutor,
)
from core.action_registry import (
    ActionRegistry,
)
from core.execution_coordinator import (
    ExecutionCoordinator,
)
from core.pipeline_context import (
    PipelineContext,
)
from core.plan_builder import (
    PlanBuilder,
)
from core.plan_executor import (
    PlanExecutor,
)
from core.result import (
    Result,
)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main() -> None:
    print()
    print("=" * 60)
    print(
        "EXECUTION COORDINATOR EXECUTE PLAN "
        "RUNTIME INTEGRATION"
    )
    print("=" * 60)

    # -----------------------------------------------------
    # REGISTRY
    # -----------------------------------------------------

    registry = ActionRegistry()

    # -----------------------------------------------------
    # ACTION: ANALYZE
    # -----------------------------------------------------

    def analyze(
        context: PipelineContext,
    ) -> Result:
        return Result.ok(
            {
                "step": "analyze",
                "request": context.input_data,
            }
        )

    # -----------------------------------------------------
    # ACTION: DESIGN
    # -----------------------------------------------------

    def design(
        context: PipelineContext,
    ) -> Result:
        return Result.ok(
            {
                "step": "design",
                "architecture": "production-ready",
            }
        )

    # -----------------------------------------------------
    # ACTION: IMPLEMENT
    # -----------------------------------------------------

    def implement(
        context: PipelineContext,
    ) -> Result:
        return Result.ok(
            {
                "step": "implement",
                "files": 3,
            }
        )

    # -----------------------------------------------------
    # ACTION: FAILURE
    # -----------------------------------------------------

    def failing(
        context: PipelineContext,
    ) -> Result:
        return Result.fail(
            "TEST_EXECUTION_FAILURE",
            "Simulated plan execution failure.",
        )

    # -----------------------------------------------------
    # REGISTER ACTIONS
    # -----------------------------------------------------

    registrations = (
        (
            "analyze",
            analyze,
        ),
        (
            "design",
            design,
        ),
        (
            "implement",
            implement,
        ),
        (
            "failing",
            failing,
        ),
    )

    for name, action in registrations:
        result = registry.register(
            name,
            action,
        )

        if result.is_failure():
            raise RuntimeError(
                f"Failed to register action: {name}"
            )

    print(
        "ACTION REGISTRY: PASS"
    )

    # -----------------------------------------------------
    # ACTION EXECUTOR
    # -----------------------------------------------------

    action_executor = ActionExecutor(
        registry
    )

    # -----------------------------------------------------
    # PLAN EXECUTOR
    # -----------------------------------------------------

    plan_executor = PlanExecutor(
        action_executor
    )

    # -----------------------------------------------------
    # EXECUTION COORDINATOR
    # -----------------------------------------------------

    coordinator = ExecutionCoordinator(
        registry_service=None,
    )

    print(
        "COORDINATOR CREATE: PASS"
    )

    # =====================================================
    # SUCCESS PATH
    # =====================================================

    execution_id = (
        "integration-execute-plan-success-001"
    )

    context = PipelineContext(
        execution_id=execution_id,
        task_id="integration-execute-plan-task-001",
    )

    context.set_input(
        "Build an AI application."
    )

    # -----------------------------------------------------
    # BUILD PLAN
    # -----------------------------------------------------

    builder = PlanBuilder(
        "Build an AI application."
    )

    builder.add_step(
        name="analyze",
        description="Analyze requirements.",
        action="analyze",
    )

    builder.add_step(
        name="design",
        description="Design architecture.",
        action="design",
    )

    builder.add_step(
        name="implement",
        description="Implement application.",
        action="implement",
    )

    plan_result = builder.build()

    if plan_result.is_failure():
        raise RuntimeError(
            plan_result.error.message
        )

    plan = plan_result.require_data()

    print(
        "PLAN BUILD: PASS"
    )

    # -----------------------------------------------------
    # START EXECUTION
    # -----------------------------------------------------

    record = coordinator.start(
        execution_id,
        task_id="integration-execute-plan-task-001",
        total_steps=3,
        metadata={
            "source": (
                "execute-plan-runtime-integration"
            ),
        },
    )

    if record.execution_id != execution_id:
        raise RuntimeError(
            "Execution ID mismatch."
        )

    if coordinator.get_runtime(
        execution_id
    ) is None:
        raise RuntimeError(
            "Runtime was not created."
        )

    print(
        "EXECUTION START + RUNTIME CREATE: PASS"
    )

    # -----------------------------------------------------
    # EXECUTE PLAN
    # -----------------------------------------------------
    #
    # PlanExecutor executes the actual actions.
    #

    result = plan_executor.execute(
        plan,
        context,
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    final_context = (
        result.require_data()
    )

    if final_context is not context:
        raise RuntimeError(
            "PlanExecutor must preserve context identity."
        )

    print(
        "PLAN EXECUTION: PASS"
    )

    # -----------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------

    if final_context.output_data != {
        "step": "implement",
        "files": 3,
    }:
        raise RuntimeError(
            "Unexpected final output."
        )

    print(
        "FINAL OUTPUT: PASS"
    )

    # -----------------------------------------------------
    # STAGE RESULTS
    # -----------------------------------------------------

    expected_stages = {
        "analyze",
        "design",
        "implement",
    }

    if set(
        final_context.stage_results
    ) != expected_stages:
        raise RuntimeError(
            "Stage results are incorrect."
        )

    print(
        "STAGE RESULTS: PASS"
    )

    # -----------------------------------------------------
    # COMPLETE EXECUTION
    # -----------------------------------------------------

    completed_record = coordinator.complete(
        execution_id,
        output=final_context.output_data,
    )

    if completed_record.status != "completed":
        raise RuntimeError(
            "Execution did not complete."
        )

    if coordinator.get_runtime(
        execution_id
    ) is not None:
        raise RuntimeError(
            "Runtime was not cleaned up."
        )

    if coordinator.is_registered(
        execution_id
    ):
        raise RuntimeError(
            "Execution remained registered."
        )

    print(
        "EXECUTION COMPLETE + RUNTIME CLEANUP: PASS"
    )

    # -----------------------------------------------------
    # AUDIT
    # -----------------------------------------------------

    audit = coordinator.get_audit(
        execution_id
    )

    if not audit:
        raise RuntimeError(
            "Execution audit should exist."
        )

    print(
        "AUDIT: PASS"
    )

    # =====================================================
    # FAILURE PATH
    # =====================================================

    failure_execution_id = (
        "integration-execute-plan-failure-001"
    )

    failure_context = PipelineContext(
        execution_id=failure_execution_id,
        task_id="integration-execute-plan-task-002",
    )

    failure_context.set_input(
        "Run failure test."
    )

    failure_builder = PlanBuilder(
        "Run failure test."
    )

    failure_builder.add_step(
        name="analyze",
        description="Analyze requirements.",
        action="analyze",
    )

    failure_builder.add_step(
        name="failing",
        description="Intentional failure.",
        action="failing",
    )

    failure_builder.add_step(
        name="implement",
        description="Must not execute.",
        action="implement",
    )

    failure_plan_result = (
        failure_builder.build()
    )

    if failure_plan_result.is_failure():
        raise RuntimeError(
            failure_plan_result.error.message
        )

    failure_plan = (
        failure_plan_result.require_data()
    )

    coordinator.start(
        failure_execution_id,
        task_id="integration-execute-plan-task-002",
        total_steps=3,
    )

    if coordinator.get_runtime(
        failure_execution_id
    ) is None:
        raise RuntimeError(
            "Failure runtime was not created."
        )

    print(
        "FAILURE EXECUTION START + RUNTIME CREATE: PASS"
    )

    # -----------------------------------------------------
    # EXECUTE FAILURE PLAN
    # -----------------------------------------------------

    failure_result = plan_executor.execute(
        failure_plan,
        failure_context,
    )

    if failure_result.is_success():
        raise RuntimeError(
            "Failure plan should return failure."
        )

    if failure_result.error.code != (
        "TEST_EXECUTION_FAILURE"
    ):
        raise RuntimeError(
            "Unexpected failure code."
        )

    print(
        "FAILURE PROPAGATION: PASS"
    )

    # -----------------------------------------------------
    # FAILED STEP
    # -----------------------------------------------------

    failed_step = (
        failure_result.error.details.get(
            "failed_step"
        )
    )

    if failed_step != "failing":
        raise RuntimeError(
            "Incorrect failed step."
        )

    print(
        "FAILED STEP DETAILS: PASS"
    )

    # -----------------------------------------------------
    # FAILURE CONTEXT
    # -----------------------------------------------------

    if failure_context.stage_results.get(
        "analyze"
    ) is None:
        raise RuntimeError(
            "Successful step result is missing."
        )

    if failure_context.stage_results.get(
        "failing"
    ) != {
        "error": (
            "Simulated plan execution failure."
        ),
    }:
        raise RuntimeError(
            "Failed step result is incorrect."
        )

    if "implement" in (
        failure_context.stage_results
    ):
        raise RuntimeError(
            "Steps after failure must not execute."
        )

    print(
        "FAILURE CONTEXT: PASS"
    )

    # -----------------------------------------------------
    # FAIL EXECUTION
    # -----------------------------------------------------

    failed_record = coordinator.fail(
        failure_execution_id,
        error_code="TEST_EXECUTION_FAILURE",
        error_message=(
            "Simulated plan execution failure."
        ),
        step_name="failing",
    )

    if failed_record.status != "failed":
        raise RuntimeError(
            "Execution did not enter failed state."
        )

    if coordinator.get_runtime(
        failure_execution_id
    ) is not None:
        raise RuntimeError(
            "Failure runtime was not cleaned up."
        )

    if coordinator.is_registered(
        failure_execution_id
    ):
        raise RuntimeError(
            "Failed execution remained registered."
        )

    print(
        "FAILURE COMPLETE + RUNTIME CLEANUP: PASS"
    )

    # -----------------------------------------------------
    # ISOLATION
    # -----------------------------------------------------

    if coordinator.active_count() != 0:
        raise RuntimeError(
            "No active executions should remain."
        )

    print(
        "EXECUTION ISOLATION: PASS"
    )

    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------

    coordinator.close()

    print(
        "CLOSE: PASS"
    )

    # -----------------------------------------------------
    # FINAL
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print(
        "EXECUTION COORDINATOR EXECUTE PLAN "
        "RUNTIME INTEGRATION: PASS"
    )
    print("=" * 60)


# ---------------------------------------------------------
# DIRECT EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":
    main()