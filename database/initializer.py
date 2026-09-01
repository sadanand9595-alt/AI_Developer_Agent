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


def initialize_database() -> None:
    """
    Create all registered database tables if they do not exist,
    then apply the minimal compatibility migration for the Task
    execution_id column on existing SQLite databases.
    """

    Base.metadata.create_all(bind=engine)
    _ensure_task_execution_id_column()


def _ensure_task_execution_id_column() -> None:
    """Add the Task.execution_id column and index when missing."""

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
                    "ALTER TABLE tasks ADD COLUMN execution_id VARCHAR(36)"
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
                    "ix_tasks_execution_id ON tasks (execution_id)"
                )
            )


def get_table_names() -> list[str]:
    """
    Return the currently available database table names.
    """

    inspector = inspect(engine)
    return inspector.get_table_names()