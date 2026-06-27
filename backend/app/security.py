"""Password hashing (pwdlib/bcrypt) and JWT issue/verify (PyJWT, HS256/RS256-ready)."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.config import settings
from app.models import User

# Explicit bcrypt hasher (avoids pwdlib's recommended() pulling in Argon2).
_password_hash = PasswordHash((BcryptHasher(),))

# A precomputed hash so a missing-user login still spends time verifying,
# normalising response time and preventing account enumeration (EC-AUTH-LGN-05).
_DUMMY_HASH = _password_hash.hash("dummy-password-for-constant-time")


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt for storage."""
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if ``password`` matches the stored bcrypt ``password_hash``."""
    return _password_hash.verify(password, password_hash)


def dummy_verify(password: str) -> None:
    """Spend comparable time when no user exists (timing-attack mitigation)."""
    _password_hash.verify(password, _DUMMY_HASH)


# --- JWT keys (algorithm-driven, RS256-ready) ------------------------------


@lru_cache
def _signing_key() -> str:
    """The key used to *sign* tokens: a PEM private key for RS*, else the HS shared secret."""
    if settings.jwt_algorithm.startswith("RS"):
        if not settings.jwt_private_key_path:
            raise RuntimeError("RS256 requires JWT_PRIVATE_KEY_PATH")
        with open(settings.jwt_private_key_path, encoding="utf-8") as fh:
            return fh.read()
    return settings.jwt_secret_key


@lru_cache
def _verify_key() -> str:
    """The key used to *verify* tokens: a PEM public key for RS*, else the HS shared secret."""
    if settings.jwt_algorithm.startswith("RS"):
        if not settings.jwt_public_key_path:
            raise RuntimeError("RS256 requires JWT_PUBLIC_KEY_PATH")
        with open(settings.jwt_public_key_path, encoding="utf-8") as fh:
            return fh.read()
    return settings.jwt_secret_key


def create_access_token(user: User) -> str:
    """Build and sign a short-lived access JWT carrying the user's id, role, and token_version."""
    now = datetime.now(UTC)
    payload = {
        "sub": user.id,
        "role": user.role.value,
        "token_version": user.token_version,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, _signing_key(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode + verify. Raises jwt.PyJWTError on any failure.

    The algorithms allowlist rejects 'none' and unexpected algs (EC-AUTH-JWT-02).
    """
    return jwt.decode(token, _verify_key(), algorithms=settings.allowed_algorithms)


# --- Opaque refresh tokens (only the hash is persisted) --------------------


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Return (raw_token, sha256_hash, expires_at)."""
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days)
    return raw, token_hash, expires_at
