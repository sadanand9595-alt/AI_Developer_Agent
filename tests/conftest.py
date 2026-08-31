"""
Shared pytest fixtures for the AI Command Center test suite.
"""

from __future__ import annotations

import pytest

from database.initializer import initialize_database


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
