from core.execution_context import ExecutionContext
from core.execution_context_registry_factory import (
    ExecutionContextRegistryFactory,
)
from core.execution_context_registry_service import (
    ExecutionContextRegistryService,
)


def test_factory_create() -> None:
    service = ExecutionContextRegistryFactory.create()

    assert isinstance(
        service,
        ExecutionContextRegistryService,
    )


def test_factory_initial_state() -> None:
    service = ExecutionContextRegistryFactory.create()

    assert service.count() == 0
    assert service.ids() == ()
    assert service.all() == ()


def test_factory_create_context() -> None:
    service = ExecutionContextRegistryFactory.create()

    context = ExecutionContext.create(
        execution_id="pytest-registry-execution-001",
        task_id="pytest-registry-task-001",
        agent_id="agent-001",
    )

    service.register(context)

    assert service.count() == 1
    assert service.get(
        context.context_id
    ) is context


def test_factory_lookup() -> None:
    service = ExecutionContextRegistryFactory.create()

    context = ExecutionContext.create(
        execution_id="pytest-registry-execution-002",
        task_id="pytest-registry-task-002",
        agent_id="agent-002",
    )

    service.register(context)

    assert service.get_by_execution(
        "pytest-registry-execution-002"
    ) is context

    assert service.contains(
        context.context_id
    )


def test_factory_isolation() -> None:
    first = ExecutionContextRegistryFactory.create()
    second = ExecutionContextRegistryFactory.create()

    context = ExecutionContext.create(
        execution_id="pytest-isolation-execution-001",
        task_id="pytest-isolation-task-001",
        agent_id="agent-001",
    )

    first.register(context)

    assert first.count() == 1
    assert second.count() == 0
    assert second.get(
        context.context_id
    ) is None


def test_factory_second_instance() -> None:
    first = ExecutionContextRegistryFactory.create()
    second = ExecutionContextRegistryFactory.create()

    context_one = ExecutionContext.create(
        execution_id="pytest-second-execution-001",
        task_id="pytest-second-task-001",
        agent_id="agent-001",
    )

    context_two = ExecutionContext.create(
        execution_id="pytest-second-execution-002",
        task_id="pytest-second-task-002",
        agent_id="agent-002",
    )

    first.register(context_one)
    second.register(context_two)

    assert first.count() == 1
    assert second.count() == 1

    assert first.get(
        context_one.context_id
    ) is context_one

    assert second.get(
        context_two.context_id
    ) is context_two


def test_factory_remove() -> None:
    service = ExecutionContextRegistryFactory.create()

    context = ExecutionContext.create(
        execution_id="pytest-remove-execution-001",
        task_id="pytest-remove-task-001",
        agent_id="agent-001",
    )

    service.register(context)

    assert service.unregister(
        context.context_id
    )

    assert service.count() == 0

    assert not service.contains(
        context.context_id
    )


def test_factory_clear() -> None:
    service = ExecutionContextRegistryFactory.create()

    context_one = ExecutionContext.create(
        execution_id="pytest-clear-execution-001",
        task_id="pytest-clear-task-001",
        agent_id="agent-001",
    )

    context_two = ExecutionContext.create(
        execution_id="pytest-clear-execution-002",
        task_id="pytest-clear-task-002",
        agent_id="agent-002",
    )

    service.register(context_one)
    service.register(context_two)

    assert service.count() == 2

    cleared = service.clear()

    assert cleared == 2
    assert service.count() == 0
    assert service.ids() == ()
    assert service.all() == ()
