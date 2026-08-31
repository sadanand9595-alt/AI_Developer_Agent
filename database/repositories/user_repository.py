"""
User repository for AI Command Center.

Provides database operations for User entities while keeping
SQLAlchemy details outside the application/service layers.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.user import User


class UserRepository:
    """Persistence operations for users."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        email: str,
        name: str,
        is_admin: bool = False,
    ) -> User:
        """Create and persist a new user."""

        if not isinstance(email, str):
            raise ValueError("Email must be a string.")

        if not isinstance(name, str):
            raise ValueError("Name must be a string.")

        normalized_email = email.strip().lower()
        normalized_name = name.strip()

        if not normalized_email:
            raise ValueError("Email cannot be empty.")

        if not normalized_name:
            raise ValueError("Name cannot be empty.")

        user = User(
            email=normalized_email,
            name=normalized_name,
            is_admin=is_admin,
        )

        self._session.add(user)
        self._session.flush()

        return user

    def get_by_id(
        self,
        user_id: str,
    ) -> User | None:
        """Return a user by ID."""

        statement = select(User).where(
            User.id == user_id
        )

        return self._session.scalar(statement)

    def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """Return a user by email."""

        if not isinstance(email, str):
            return None

        normalized_email = email.strip().lower()

        statement = select(User).where(
            User.email == normalized_email
        )

        return self._session.scalar(statement)

    def list_active(
        self,
    ) -> list[User]:
        """Return all active users."""

        statement = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.asc())
        )

        return list(
            self._session.scalars(statement).all()
        )

    def update_name(
        self,
        user: User,
        name: str,
    ) -> User:
        """Update a user's display name."""

        if not isinstance(name, str):
            raise ValueError("Name must be a string.")

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Name cannot be empty."
            )

        user.name = normalized_name
        self._session.flush()

        return user

    def deactivate(
        self,
        user: User,
    ) -> User:
        """Deactivate a user."""

        user.is_active = False
        self._session.flush()

        return user