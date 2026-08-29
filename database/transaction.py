"""
Transaction management for AI Command Center.

Provides reusable transaction helpers for database operations.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

from database.session import create_session


T = TypeVar("T")


def execute_transaction(
    operation: Callable[[Session], T],
) -> T:
    """
    Execute a database operation inside a transaction.

    The transaction is committed when the operation succeeds.
    It is rolled back automatically when an exception occurs.
    """

    session = create_session()

    try:
        result = operation(session)
        session.commit()
        return result

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def execute_read(
    operation: Callable[[Session], T],
) -> T:
    """
    Execute a read-only database operation.

    The session is closed automatically after completion.
    """

    session = create_session()

    try:
        return operation(session)

    finally:
        session.close()