"""
Authentication endpoints: register and login.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from api.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from database.models.user import User
from services.user_service import UserService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    """
    Register a new user account.

    Duplicate emails are rejected with 400 by the existing
    UserService.create_user() contract (translated by the global
    ValueError handler).
    """

    service = UserService(db)

    return service.create_user(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email/password and issue a JWT."""

    service = UserService(db)

    user = service.get_user_by_email(payload.email)

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None or not user.is_active:
        raise invalid_credentials

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise invalid_credentials

    return TokenResponse(
        access_token=create_access_token(user.id)
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the authenticated user's own profile."""

    return current_user
