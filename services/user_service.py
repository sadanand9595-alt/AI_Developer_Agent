"""
User service for AI Command Center.

Contains business logic for user creation, lookup, updating,
activation, and deactivation.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.user import User
from database.repositories.user_repository import UserRepository


class UserService:
    """Business operations for users."""

    def __init__(self, session: Session) -> None:
        self._repository = UserRepository(session)

    def create_user(
        self,
        *,
        email: str,
        name: str,
        password_hash: str,
        is_admin: bool = False,
    ) -> User:
        """
        Create a new user.

        Raises:
            ValueError: If the email is already registered.
        """

        if not isinstance(email, str):
            raise ValueError("Email must be a string.")

        normalized_email = email.strip().lower()

        existing_user = self._repository.get_by_email(
            normalized_email
        )

        if existing_user is not None:
            raise ValueError(
                "A user with this email already exists."
            )

        return self._repository.create(
            email=normalized_email,
            name=name,
            password_hash=password_hash,
            is_admin=is_admin,
        )

    def get_user(
        self,
        user_id: str,
    ) -> User | None:
        """Get a user by ID."""

        return self._repository.get_by_id(user_id)

    def get_user_by_email(
        self,
        email: str,
    ) -> User | None:
        """Get a user by email."""

        if not isinstance(email, str):
            return None

        return self._repository.get_by_email(
            email.strip().lower()
        )

    def list_active_users(self) -> list[User]:
        """Return all active users."""

        return self._repository.list_active()

    def update_name(
        self,
        user_id: str,
        name: str,
    ) -> User:
        """Update a user's name."""

        user = self._repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        return self._repository.update_name(
            user,
            name,
        )

    def deactivate_user(
        self,
        user_id: str,
    ) -> User:
        """Deactivate a user."""

        user = self._repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        if not user.is_active:
            return user

        return self._repository.deactivate(user)