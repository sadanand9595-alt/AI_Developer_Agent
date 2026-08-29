"""
Database session utilities for AI Command Center.

Provides a controlled session factory and context manager so
database lifecycle management remains consistent across the
API, workers, agents, and background jobs.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from database.connection import SessionLocal


def create_session() -> Session:
    """
    Create a new database session.

    The caller is responsible for closing the returned session.
    """

    return SessionLocal()


def get_session() -> Generator[Session, None, None]:
    """
    Yield a database session and close it automatically.
    """

    session = create_session()

    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transaction-aware database session.

    Commits when the operation succeeds and rolls back when an
    exception occurs.
    """

    session = create_session()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()