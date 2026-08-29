"""
Concurrency and thread-safety tests for execution architecture.

Tests cover:
- ActionRegistry concurrent operations
- ExecutionRegistry concurrent operations
- ExecutionContextRegistry concurrent operations
- ExecutionManager concurrent operations
- ExecutionTracker concurrent operations
- ExecutionEventBus concurrent operations
- EventBus exception isolation
"""

from __future__ import annotations

import asyncio
import threading
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.action_registry import ActionRegistry
from core.execution_registry import ExecutionRegistry
from core.execution_context_registry import ExecutionContextRegistry
from core.execution_context import ExecutionContext
from core.execution_manager import ExecutionManager
from core.execution_tracker import ExecutionTracker
from core.execution_event import ExecutionEvent, ExecutionEventType
from core.execution_event_bus import ExecutionEventBus
from core.event_bus import EventBus


# ---------------------------------------------------------------------------
# Simple Event class for EventBus tests
# ---------------------------------------------------------------------------

class SimpleEvent:
    """Minimal event for EventBus testing."""

    def __init__(self, event_type: str) -> None:
        self.event_type = event_type


class EventType:
    """Test event types."""

    TEST = "test"
    OTHER = "other"


# ---------------------------------------------------------------------------
# ActionRegistry concurrency tests
# ---------------------------------------------------------------------------

def test_action_registry_concurrent_register_and_get() -> None:
    """Concurrent register and get operations are safe."""
    registry = ActionRegistry()
    num_threads = 20
    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            name = f"action_{idx}"

            def handler() -> str:
                return "ok"

            result = registry.register(name, handler)
            if result.is_failure():
                errors.append(
                    f"Register failed for {name}: {result.error.message}"
                )
                return

            get_result = registry.get(name)
            if get_result.is_failure():
                errors.append(
                    f"Get failed for {name}: {get_result.error.message}"
                )
            elif get_result.data != handler:
                errors.append(f"Handler mismatch for {name}")
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert registry.count() == num_threads
    for i in range(num_threads):
        assert registry.contains(f"action_{i}")


def test_action_registry_concurrent_unregister() -> None:
    """Concurrent unregister operations are safe."""
    registry = ActionRegistry()
    num_threads = 20

    # Pre-register
    for i in range(num_threads):
        registry.register(f"action_{i}", lambda: None)

    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            name = f"action_{idx}"
            registry.unregister(name)

            # Verify it's gone
            get_result = registry.get(name)
            if get_result.is_success():
                errors.append(
                    f"Action {name} still registered after unregister"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert registry.count() == 0


def test_action_registry_concurrent_clear_and_get() -> None:
    """Concurrent clear and get operations are safe."""
    registry = ActionRegistry()
    num_items = 10

    for i in range(num_items):
        registry.register(f"action_{i}", lambda: None)

    barrier = threading.Barrier(2)
    errors: list[str] = []

    def clearer() -> None:
        try:
            barrier.wait()
            registry.clear()
        except Exception as exc:
            errors.append(f"Clearer exception: {exc}")

    def getter() -> None:
        try:
            barrier.wait()
            for i in range(num_items):
                registry.get(f"action_{i}")
        except Exception as exc:
            errors.append(f"Getter exception: {exc}")

    t1 = threading.Thread(target=clearer)
    t2 = threading.Thread(target=getter)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Errors: {errors}"


# ---------------------------------------------------------------------------
# ExecutionRegistry concurrency tests
# ---------------------------------------------------------------------------

def test_execution_registry_concurrent_register_and_get() -> None:
    """Concurrent register and get operations are safe."""
    registry = ExecutionRegistry()
    num_threads = 20
    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            exec_id = f"exec_{idx}"
            data = f"data_{idx}"
            registry.register(exec_id, data)
            retrieved = registry.get(exec_id)
            if retrieved != data:
                errors.append(f"Data mismatch for {exec_id}")
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert registry.count() == num_threads
    for i in range(num_threads):
        assert registry.contains(f"exec_{i}")


def test_execution_registry_concurrent_unregister() -> None:
    """Concurrent unregister operations are safe."""
    registry = ExecutionRegistry()
    num_threads = 20

    for i in range(num_threads):
        registry.register(f"exec_{i}", f"data_{i}")

    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            exec_id = f"exec_{idx}"
            registry.unregister(exec_id)
            if registry.contains(exec_id):
                errors.append(
                    f"Execution {exec_id} still registered after unregister"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert registry.count() == 0


def test_execution_registry_concurrent_clear_and_get() -> None:
    """Concurrent clear and get operations are safe."""
    registry = ExecutionRegistry()
    num_items = 10

    for i in range(num_items):
        registry.register(f"exec_{i}", f"data_{i}")

    barrier = threading.Barrier(2)
    errors: list[str] = []

    def clearer() -> None:
        try:
            barrier.wait()
            registry.clear()
        except Exception as exc:
            errors.append(f"Clearer exception: {exc}")

    def getter() -> None:
        try:
            barrier.wait()
            for i in range(num_items):
                registry.get(f"exec_{i}")
        except Exception as exc:
            errors.append(f"Getter exception: {exc}")

    t1 = threading.Thread(target=clearer)
    t2 = threading.Thread(target=getter)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Errors: {errors}"


# ---------------------------------------------------------------------------
# ExecutionContextRegistry concurrency tests
# ---------------------------------------------------------------------------

def test_execution_context_registry_concurrent_register_and_get() -> None:
    """Concurrent register and get operations are safe."""
    registry = ExecutionContextRegistry()
    num_threads = 20
    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            context = ExecutionContext.create(
                user_id=f"user_{idx}",
                task_id=f"task_{idx}",
                execution_id=f"exec_{idx}",
            )
            registry.register(context)

            retrieved = registry.get(context.context_id)
            if retrieved is not context:
                errors.append(
                    f"Context mismatch for {context.context_id}"
                )

            retrieved_by_exec = registry.get_by_execution(
                f"exec_{idx}"
            )
            if retrieved_by_exec is not context:
                errors.append(
                    f"Context by exec mismatch for {context.context_id}"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert registry.count() == num_threads


def test_execution_context_registry_concurrent_unregister() -> None:
    """Concurrent unregister operations are safe."""
    registry = ExecutionContextRegistry()
    num_threads = 20

    contexts: list[ExecutionContext] = []
    for i in range(num_threads):
        ctx = ExecutionContext.create(
            user_id=f"user_{i}",
            task_id=f"task_{i}",
            execution_id=f"exec_{i}",
        )
        contexts.append(ctx)
        registry.register(ctx)

    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            context = contexts[idx]
            registry.unregister(context.context_id)
            if registry.contains(context.context_id):
                errors.append(
                    f"Context {context.context_id} still registered"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert registry.count() == 0


def test_execution_context_registry_concurrent_clear_and_get() -> None:
    """Concurrent clear and get operations are safe."""
    registry = ExecutionContextRegistry()
    num_items = 10

    for i in range(num_items):
        ctx = ExecutionContext.create(
            user_id=f"user_{i}",
            task_id=f"task_{i}",
            execution_id=f"exec_{i}",
        )
        registry.register(ctx)

    barrier = threading.Barrier(2)
    errors: list[str] = []

    def clearer() -> None:
        try:
            barrier.wait()
            registry.clear()
        except Exception as exc:
            errors.append(f"Clearer exception: {exc}")

    def getter() -> None:
        try:
            barrier.wait()
            for i in range(num_items):
                registry.get_by_execution(f"exec_{i}")
        except Exception as exc:
            errors.append(f"Getter exception: {exc}")

    t1 = threading.Thread(target=clearer)
    t2 = threading.Thread(target=getter)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Errors: {errors}"


# ---------------------------------------------------------------------------
# ExecutionManager concurrency tests
# ---------------------------------------------------------------------------

def test_execution_manager_concurrent_start_and_complete() -> None:
    """Concurrent start and complete operations are safe."""
    manager = ExecutionManager()
    num_threads = 20
    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            exec_id = f"exec_{idx}"
            record = manager.start(exec_id, task_id=f"task_{idx}")

            retrieved = manager.get(exec_id)
            if retrieved is not record:
                errors.append(f"Record mismatch for {exec_id}")

            manager.complete(exec_id, output=f"output_{idx}")

            retrieved = manager.get(exec_id)
            if retrieved is None or retrieved.status != "completed":
                errors.append(
                    f"Status not completed for {exec_id}"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert manager.count() == num_threads
    assert manager.active_count() == 0


def test_execution_manager_concurrent_start_and_fail() -> None:
    """Concurrent start and fail operations are safe."""
    manager = ExecutionManager()
    num_threads = 20
    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            exec_id = f"exec_{idx}"
            manager.start(exec_id, task_id=f"task_{idx}")
            manager.fail(
                exec_id,
                error_code="TEST_ERROR",
                error_message="Test failure",
            )

            retrieved = manager.get(exec_id)
            if retrieved is None or retrieved.status != "failed":
                errors.append(
                    f"Status not failed for {exec_id}"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert manager.count() == num_threads
    assert manager.active_count() == 0


def test_execution_manager_concurrent_clear_completed() -> None:
    """Concurrent clear_completed operations are safe."""
    manager = ExecutionManager()
    num_threads = 20

    # Create and complete executions
    for i in range(num_threads):
        exec_id = f"exec_{i}"
        manager.start(exec_id)
        manager.complete(exec_id)

    barrier = threading.Barrier(2)
    errors: list[str] = []

    def clearer() -> None:
        try:
            barrier.wait()
            manager.clear_completed()
        except Exception as exc:
            errors.append(f"Clearer exception: {exc}")

    def getter() -> None:
        try:
            barrier.wait()
            for i in range(num_threads):
                manager.get(f"exec_{i}")
        except Exception as exc:
            errors.append(f"Getter exception: {exc}")

    t1 = threading.Thread(target=clearer)
    t2 = threading.Thread(target=getter)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Errors: {errors}"


# ---------------------------------------------------------------------------
# ExecutionTracker concurrency tests
# ---------------------------------------------------------------------------

def test_execution_tracker_concurrent_steps() -> None:
    """Concurrent start_step and complete_step operations are safe."""
    tracker = ExecutionTracker()
    exec_id = "exec_1"
    total_steps = 20
    tracker.start(exec_id, total_steps=total_steps)

    barrier = threading.Barrier(total_steps)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            step_name = f"step_{idx}"
            tracker.start_step(exec_id, step_name)
            tracker.complete_step(exec_id, step_name)
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(total_steps)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    progress = tracker.get(exec_id)
    assert progress is not None
    assert progress.completed_steps == total_steps
    assert progress.status == "completed"
    assert not errors, f"Errors: {errors}"


def test_execution_tracker_concurrent_fail_and_cancel() -> None:
    """Concurrent fail and cancel operations are safe."""
    tracker = ExecutionTracker()
    num_threads = 20
    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            exec_id = f"exec_{idx}"
            tracker.start(exec_id, total_steps=1)
            tracker.start_step(exec_id, "step_0")

            # Alternate between fail and cancel
            if idx % 2 == 0:
                tracker.fail(exec_id, step_name="step_0")
            else:
                tracker.cancel(exec_id)

            progress = tracker.get(exec_id)
            if progress is None:
                errors.append(f"Progress missing for {exec_id}")
            elif idx % 2 == 0 and progress.status != "failed":
                errors.append(
                    f"Status not failed for {exec_id}"
                )
            elif idx % 2 == 1 and progress.status != "cancelled":
                errors.append(
                    f"Status not cancelled for {exec_id}"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert tracker.count() == num_threads


def test_execution_tracker_concurrent_remove() -> None:
    """Concurrent remove operations are safe."""
    tracker = ExecutionTracker()
    num_threads = 20

    for i in range(num_threads):
        tracker.start(f"exec_{i}", total_steps=1)

    barrier = threading.Barrier(num_threads)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            exec_id = f"exec_{idx}"
            tracker.remove(exec_id)
            if tracker.get(exec_id) is not None:
                errors.append(
                    f"Execution {exec_id} still tracked after remove"
                )
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert tracker.count() == 0


# ---------------------------------------------------------------------------
# ExecutionEventBus concurrency tests
# ---------------------------------------------------------------------------

def test_execution_event_bus_concurrent_subscribe_and_publish() -> None:
    """Concurrent subscribe and publish operations are safe."""
    bus = ExecutionEventBus()
    num_listeners = 20
    barrier = threading.Barrier(num_listeners)
    received: list[str] = []
    lock = threading.Lock()

    def listener(event: ExecutionEvent) -> None:
        with lock:
            received.append(event.execution_id)

    def subscribe_worker() -> None:
        barrier.wait()
        bus.subscribe(listener)

    # Subscribe concurrently
    threads = [
        threading.Thread(target=subscribe_worker)
        for _ in range(num_listeners)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Publish event
    event = ExecutionEvent.create(
        event_type=ExecutionEventType.STARTED,
        execution_id="exec_1",
    )
    notified = bus.publish(event)

    # All listeners should receive the event
    assert notified == num_listeners
    assert len(received) == num_listeners
    for r in received:
        assert r == "exec_1"


def test_execution_event_bus_concurrent_unsubscribe() -> None:
    """Concurrent unsubscribe operations are safe."""
    bus = ExecutionEventBus()
    num_listeners = 20
    listeners: list[callable] = []

    for _ in range(num_listeners):
        listener = lambda e: None
        listeners.append(listener)
        bus.subscribe(listener)

    barrier = threading.Barrier(num_listeners)
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            bus.unsubscribe(listeners[idx])
        except Exception as exc:
            errors.append(f"Worker {idx} exception: {exc}")

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_listeners)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors: {errors}"
    assert bus.listener_count() == 0


def test_execution_event_bus_exception_isolation() -> None:
    """EventBus isolates listener exceptions; other listeners still receive events."""
    bus = ExecutionEventBus()
    received: list[str] = []
    lock = threading.Lock()

    def raising_listener(event: ExecutionEvent) -> None:
        raise ValueError("Intentional failure")

    def good_listener(event: ExecutionEvent) -> None:
        with lock:
            received.append(event.execution_id)

    bus.subscribe(raising_listener)
    bus.subscribe(good_listener)

    event = ExecutionEvent.create(
        event_type=ExecutionEventType.STARTED,
        execution_id="exec_1",
    )

    # Should not raise despite the raising listener
    notified = bus.publish(event)

    # Both listeners were attempted
    assert notified == 2
    # Good listener received the event
    assert len(received) == 1
    assert received[0] == "exec_1"


# ---------------------------------------------------------------------------
# EventBus exception isolation tests
# ---------------------------------------------------------------------------

def test_event_bus_exception_isolation_sync() -> None:
    """EventBus isolates synchronous listener exceptions."""
    bus = EventBus()
    received: list[str] = []
    lock = threading.Lock()

    def raising_listener(event: Any) -> None:
        raise ValueError("Intentional failure")

    def good_listener(event: Any) -> None:
        with lock:
            received.append(event.event_type)

    bus.subscribe(EventType.TEST, raising_listener)
    bus.subscribe(EventType.TEST, good_listener)

    # Run async publish in an event loop
    async def run_test() -> None:
        await bus.publish(SimpleEvent(EventType.TEST))

    asyncio.run(run_test())

    # Good listener should have received the event
    assert len(received) == 1
    assert received[0] == EventType.TEST


def test_event_bus_exception_isolation_async() -> None:
    """EventBus isolates asynchronous listener exceptions."""
    bus = EventBus()
    received: list[str] = []
    lock = threading.Lock()

    async def raising_listener(event: Any) -> None:
        raise ValueError("Intentional failure")

    async def good_listener(event: Any) -> None:
        with lock:
            received.append(event.event_type)

    bus.subscribe(EventType.TEST, raising_listener)
    bus.subscribe(EventType.TEST, good_listener)

    async def run_test() -> None:
        await bus.publish(SimpleEvent(EventType.TEST))

    asyncio.run(run_test())

    assert len(received) == 1
    assert received[0] == EventType.TEST


def test_event_bus_publish_parallel_exception_isolation() -> None:
    """EventBus publish_parallel isolates listener exceptions."""
    bus = EventBus()
    received: list[str] = []
    lock = threading.Lock()

    def raising_listener(event: Any) -> None:
        raise ValueError("Intentional failure")

    def good_listener(event: Any) -> None:
        with lock:
            received.append(event.event_type)

    bus.subscribe(EventType.TEST, raising_listener)
    bus.subscribe(EventType.TEST, good_listener)

    async def run_test() -> None:
        await bus.publish_parallel(SimpleEvent(EventType.TEST))

    asyncio.run(run_test())

    assert len(received) == 1
    assert received[0] == EventType.TEST
