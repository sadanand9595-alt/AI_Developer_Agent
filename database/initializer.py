"""
Database initialization utilities for AI Command Center.

Provides controlled database initialization for development
and test environments.
"""

from __future__ import annotations

from sqlalchemy import inspect, text

from database.base import Base
from database.connection import engine
from database import models  # noqa: F401
from database.repositories.task_repository import TaskRepository
from database.session import session_scope


def initialize_database() -> None:
    """
    Create all registered database tables if they do not exist,
    then apply the minimal compatibility migration for the Task
    execution_id and lease columns on existing SQLite databases.
    """

    Base.metadata.create_all(bind=engine)
    _ensure_task_execution_id_column()
    _ensure_task_lease_columns()
    _ensure_task_lease_owner_id_column()
    _ensure_approval_execution_columns()
    _reconcile_expired_running_tasks()


def _ensure_task_execution_id_column() -> None:
    """Ensure Task.execution_id exists with sufficient capacity."""

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "tasks" not in table_names:
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("tasks")
    }

    if "execution_id" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE tasks "
                    "ADD COLUMN execution_id VARCHAR(255)"
                )
            )
    else:
        # Existing databases may have the old VARCHAR(36) column.
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE tasks "
                    "ALTER COLUMN execution_id TYPE VARCHAR(255)"
                )
            )

    indexes = {
        index["name"]
        for index in inspector.get_indexes("tasks")
    }

    if "ix_tasks_execution_id" not in indexes:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS "
                    "ix_tasks_execution_id "
                    "ON tasks (execution_id)"
                )
            )


def _ensure_task_lease_columns() -> None:
    """Add Task lease metadata columns when missing."""

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "tasks" not in table_names:
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("tasks")
    }

    if "lease_expires_at" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE tasks ADD COLUMN lease_expires_at DATETIME"
                )
            )

    if "last_heartbeat_at" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE tasks ADD COLUMN last_heartbeat_at DATETIME"
                )
            )


def _ensure_task_lease_owner_id_column() -> None:
    """Add Task.lease_owner_id when the existing database is missing it."""

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "tasks" not in table_names:
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("tasks")
    }

    if "lease_owner_id" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE tasks ADD COLUMN lease_owner_id VARCHAR(255)"
                )
            )

    indexes = {
        index["name"]
        for index in inspector.get_indexes("tasks")
    }

    if "ix_tasks_lease_owner_id" not in indexes:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS "
                    "ix_tasks_lease_owner_id ON tasks (lease_owner_id)"
                )
            )


def _reconcile_expired_running_tasks() -> None:
    """Fail stale RUNNING tasks whose durable lease has already expired."""

    with session_scope() as session:
        repository = TaskRepository(session)
        repository.reconcile_expired_running_tasks()


def _ensure_approval_execution_columns() -> None:
    """Add execution resume metadata to existing approval databases."""

    inspector = inspect(engine)
    if "approval_requests" not in set(inspector.get_table_names()):
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("approval_requests")
    }
    additions = {
        "execution_id": "VARCHAR(255)",
        "plan_id": "VARCHAR(36)",
        "step_id": "VARCHAR(36)",
    }
    with engine.begin() as connection:
        for name, sql_type in additions.items():
            if name not in columns:
                connection.execute(
                    text(
                        f"ALTER TABLE approval_requests "
                        f"ADD COLUMN {name} {sql_type}"
                    )
                )


def get_table_names() -> list[str]:
    """
    Return the currently available database table names.
    """

    inspector = inspect(engine)
    return inspector.get_table_names()