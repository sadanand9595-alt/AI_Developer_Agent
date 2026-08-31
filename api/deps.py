"""
FastAPI dependencies: database session and current-user resolution.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.models.user import User
from database.repositories.user_repository import UserRepository
from database.session import session_scope
from api.security import InvalidTokenError, decode_access_token


_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Yield a request-scoped database session.

    Reuses the existing, already-audited session_scope() contract:
    commits on success, rolls back on any exception, always closes.
    """

    with session_scope() as session:
        yield session


def get_current_user(
    token: str | None = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the authenticated user from a bearer token.

    Raises:
        HTTPException(401): Missing/invalid/expired token, or the
            token refers to a user that no longer exists or has
            been deactivated.
    """

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise unauthorized

    try:
        user_id = decode_access_token(token)
    except InvalidTokenError as exc:
        raise unauthorized from exc

    user = UserRepository(db).get_by_id(user_id)

    if user is None or not user.is_active:
        raise unauthorized

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to be an administrator."""

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required.",
        )

    return current_user
