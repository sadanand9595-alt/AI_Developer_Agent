"""
Shared pytest fixtures for the AI Command Center test suite.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from database.initializer import initialize_database
from database.repositories.task_repository import TaskRepository
from database.session import session_scope


@pytest.fixture(scope="session", autouse=True)
def _ensure_database_schema() -> None:
    """
    Ensure all SQLAlchemy tables exist before any test runs.

    A fresh checkout (e.g. a CI runner) has no database file and no
    schema -- only data/.gitkeep is tracked, deliberately, since a
    populated database must never be committed. Locally this always
    worked by accident because data/command_center.db already had
    tables from prior manual/dev runs.

    Reuses the existing, already-audited initialize_database()
    (Base.metadata.create_all(bind=engine), idempotent -- safe to
    call again even when tables already exist) instead of
    duplicating schema definitions here. Runs once per test session,
    before the first test; it does not reset or drop anything
    between tests, so existing test isolation (unique per-test data
    via uuid4()-suffixed emails/etc., already used throughout this
    suite) is unchanged.
    """

    initialize_database()


@pytest.fixture(autouse=True)
def _isolate_running_task_leases():
    """Prevent durable running leases from leaking between tests."""

    _reconcile_all_running_tasks()
    yield
    _reconcile_all_running_tasks()


def _reconcile_all_running_tasks() -> None:
    """Finish any test-created running leases before the next test."""

    with session_scope() as session:
        TaskRepository(session).reconcile_expired_running_tasks(
            now=datetime.now(timezone.utc) + timedelta(days=3650)
        )
