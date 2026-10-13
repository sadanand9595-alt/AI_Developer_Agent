from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from database.repositories.task_repository import TaskRepository
from database.repositories.user_repository import UserRepository
from database.session import session_scope


@pytest.mark.parametrize(
    "operation",
    ["heartbeat", "checkpoint", "complete", "fail"],
)
def test_expired_lease_rejects_execution_transitions(operation):
    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"expired-lease-{uuid4().hex}@example.com",
            name="Expired Lease Test User",
            password_hash="test-hash-not-used",
        )

        repository = TaskRepository(session)
        task = repository.create(
            user_id=user.id,
            title=f"Expired lease {operation}",
            description="Regression test for expired execution leases.",
        )

        execution_id = f"execution-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
            lease_ttl_seconds=300,
        )

        task.lease_expires_at = (
            datetime.now(timezone.utc) - timedelta(seconds=60)
        )
        session.flush()
        session.refresh(task)

        assert task.lease_expires_at <= datetime.now(timezone.utc)

        with pytest.raises(ValueError):
            if operation == "heartbeat":
                repository.heartbeat(
                    task,
                    execution_id=execution_id,
                    lease_owner_id=execution_id,
                )
            elif operation == "checkpoint":
                repository.save_orchestration_checkpoint(
                    task,
                    {"status": "completed"},
                    execution_id=execution_id,
                    lease_owner_id=execution_id,
                )
            elif operation == "complete":
                repository.mark_completed(
                    task,
                    {"message": "Must be rejected"},
                    execution_id=execution_id,
                    lease_owner_id=execution_id,
                )
            else:
                repository.mark_failed(
                    task,
                    {"error": "Must be rejected"},
                    execution_id=execution_id,
                    lease_owner_id=execution_id,
                )

        session.refresh(task)

        assert task.status == "running"
        assert task.execution_id == execution_id
        assert task.lease_owner_id == execution_id
        assert task.lease_expires_at <= datetime.now(timezone.utc)
