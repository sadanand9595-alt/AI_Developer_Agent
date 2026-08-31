"""
Password hashing and JWT token handling for the API layer.

Password hashing uses stdlib hashlib.pbkdf2_hmac (no extra native
dependency, no build-toolchain risk). JWT uses PyJWT with the
existing settings.jwt_secret / settings.jwt_access_expires_minutes
already defined in config/settings.py.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from config.settings import settings


_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 260_000
_SALT_BYTES = 16


class InvalidTokenError(Exception):
    """Raised when a bearer token is missing, malformed, or expired."""


def hash_password(password: str) -> str:
    """
    Hash a plaintext password.

    Returns a self-describing string of the form:
        pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """

    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    salt = secrets.token_hex(_SALT_BYTES)

    derived = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    )

    return (
        f"pbkdf2_{_PBKDF2_ALGORITHM}$"
        f"{_PBKDF2_ITERATIONS}$"
        f"{salt}$"
        f"{derived.hex()}"
    )


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Return whether a plaintext password matches a stored hash."""

    if not isinstance(password, str) or not password:
        return False

    if not isinstance(password_hash, str):
        return False

    parts = password_hash.split("$")

    if len(parts) != 4:
        return False

    algorithm_label, iterations_str, salt, expected_hex = parts

    if not algorithm_label.startswith("pbkdf2_"):
        return False

    algorithm = algorithm_label[len("pbkdf2_"):]

    try:
        iterations = int(iterations_str)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac(
        algorithm,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )

    return hmac.compare_digest(derived.hex(), expected_hex)


def create_access_token(user_id: str) -> str:
    """Create a signed JWT access token for a user ID."""

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now
        + timedelta(
            minutes=settings.jwt_access_expires_minutes
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> str:
    """
    Decode a JWT access token and return the user ID (``sub``).

    Raises:
        InvalidTokenError: If the token is missing, malformed,
            expired, or has an invalid signature.
    """

    if not isinstance(token, str) or not token:
        raise InvalidTokenError("Token cannot be empty.")

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(
            "Token is invalid or expired."
        ) from exc

    user_id = payload.get("sub")

    if not isinstance(user_id, str) or not user_id:
        raise InvalidTokenError(
            "Token does not contain a valid subject."
        )

    return user_id
