"""
Database connection management for AI Command Center.

The database URL is provided by the application settings.
The connection layer is intentionally isolated so the rest of
the application does not depend directly on the database engine.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings


def _create_engine() -> Engine:
    """Create the SQLAlchemy engine from application settings."""

    connect_args: dict[str, object] = {}
    is_sqlite = settings.database_url.startswith("sqlite")

    if is_sqlite:
        connect_args["check_same_thread"] = False

    created_engine = create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )

    if is_sqlite:
        # SQLite does not enforce foreign key constraints (or
        # the ondelete="CASCADE"/"SET NULL" behavior declared on
        # every model in this project) unless explicitly enabled
        # per connection. Without this, records can reference
        # nonexistent parents (e.g. an audit log with a dangling
        # user_id) with no error.
        @event.listens_for(created_engine, "connect")
        def _enable_sqlite_foreign_keys(
            dbapi_connection,
            connection_record,
        ) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return created_engine


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