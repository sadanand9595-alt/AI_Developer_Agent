"""
Database connection management for AI Command Center.

The database URL is provided by the application settings.
The connection layer is intentionally isolated so the rest of
the application does not depend directly on the database engine.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings


def _create_engine() -> Engine:
    """Create the SQLAlchemy engine from application settings."""

    connect_args: dict[str, object] = {}

    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


engine: Engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    """
    Provide a database session.

    The session is always closed after the caller finishes using it.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()