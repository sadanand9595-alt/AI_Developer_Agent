from core.execution_context_coordinator import (
    ExecutionContextCoordinator,
)
from core.execution_context_coordinator_factory import (
    ExecutionContextCoordinatorFactory,
)


def test_factory_create() -> None:
    coordinator = (
        ExecutionContextCoordinatorFactory.create()
    )

    assert isinstance(
        coordinator,
        ExecutionContextCoordinator,
    )


def test_factory_initial_state() -> None:
    coordinator = (
        ExecutionContextCoordinatorFactory.create()
    )

    assert coordinator.count() == 0
    assert coordinator.ids() == ()
    assert coordinator.all() == ()


def test_factory_create_and_lookup() -> None:
    coordinator = (
        ExecutionContextCoordinatorFactory.create()
    )

    context = coordinator.create(
        "pytest-coordinator-001"
    )

    assert coordinator.count() == 1

    assert coordinator.contains(
        "pytest-coordinator-001"
    )

    assert coordinator.get(
        "pytest-coordinator-001"
    ) is context


def test_factory_update() -> None:
    coordinator = (
        ExecutionContextCoordinatorFactory.create()
    )

    context = coordinator.create(
        "pytest-coordinator-002"
    )

    updated = coordinator.update_metadata(
        "pytest-coordinator-002",
        {"mode": "test"},
    )

    assert updated is context

    assert context.metadata.get(
        "mode"
    ) == "test"


def test_factory_isolation() -> None:
    first = (
        ExecutionContextCoordinatorFactory.create()
    )

    second = (
        ExecutionContextCoordinatorFactory.create()
    )

    first.create(
        "pytest-isolation-001"
    )

    assert first.count() == 1
    assert second.count() == 0

    assert second.get(
        "pytest-isolation-001"
    ) is None


def test_factory_second_instance() -> None:
    first = (
        ExecutionContextCoordinatorFactory.create()
    )

    second = (
        ExecutionContextCoordinatorFactory.create()
    )

    first.create(
        "pytest-first-001"
    )

    second.create(
        "pytest-second-001"
    )

    assert first.count() == 1
    assert second.count() == 1

    assert first.contains(
        "pytest-first-001"
    )

    assert not first.contains(
        "pytest-second-001"
    )

    assert second.contains(
        "pytest-second-001"
    )

    assert not second.contains(
        "pytest-first-001"
    )


def test_factory_remove() -> None:
    coordinator = (
        ExecutionContextCoordinatorFactory.create()
    )

    coordinator.create(
        "pytest-remove-001"
    )

    removed = coordinator.remove(
        "pytest-remove-001"
    )

    assert removed is True
    assert coordinator.count() == 0

    assert not coordinator.contains(
        "pytest-remove-001"
    )


def test_factory_clear() -> None:
    coordinator = (
        ExecutionContextCoordinatorFactory.create()
    )

    coordinator.create(
        "pytest-clear-001"
    )

    coordinator.create(
        "pytest-clear-002"
    )

    assert coordinator.count() == 2

    cleared = coordinator.clear()

    assert cleared == 2
    assert coordinator.count() == 0
    assert coordinator.ids() == ()
    assert coordinator.all() == ()
