"""
Database initialization utilities for AI Command Center.

Provides controlled database initialization for development
and test environments.
"""

from __future__ import annotations

from sqlalchemy import inspect

from database.base import Base
from database.connection import engine
from database import models  # noqa: F401


def initialize_database() -> None:
    """
    Create all registered database tables if they do not exist.
    """

    Base.metadata.create_all(bind=engine)


def get_table_names() -> list[str]:
    """
    Return the currently available database table names.
    """

    inspector = inspect(engine)
    return inspector.get_table_names()