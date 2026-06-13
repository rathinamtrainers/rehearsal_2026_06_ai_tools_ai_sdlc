"""JWT access tokens (PyJWT) and opaque refresh tokens.

Access-token claims follow AC-AUTH-07: ``sub`` (user UUID), ``role``, ``iat``,
``exp`` (iat + TTL), ``jti`` (unique id for future revocation tracking), plus
``tv`` (token_version) reserved for bulk invalidation after a password reset.

HS256 today. Everything algorithm-specific is funnelled through ``_signing_key`` /
``_verify_key`` and ``settings.jwt_algorithm`` so moving to RS256 is a config change
(point the keys at a PEM keypair) rather than a rewrite. Decoding always passes an
explicit ``algorithms`` allowlist, so ``alg:none`` and algorithm-confusion are rejected
(EC-AUTH-JWT-02).
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from .config import settings
from .models import User


def _signing_key() -> str:
    # RS256 would return the private key here instead.
    return settings.jwt_secret


def _verify_key() -> str:
    # RS256 would return the public key here instead.
    return settings.jwt_secret


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        "jti": uuid.uuid4().hex,
        "tv": user.token_version,
    }
    return jwt.encode(payload, _signing_key(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Return the verified claims, or raise ``jwt.PyJWTError`` on invalid/expired."""
    return jwt.decode(token, _verify_key(), algorithms=[settings.jwt_algorithm])


def create_refresh_token() -> str:
    """Opaque, high-entropy refresh token.

    Issued at login to satisfy the client's response shape. Server-side persistence
    and rotation (BRD ``refresh_tokens`` table, AC-AUTH-08) are a later iteration —
    this value is not yet stored or accepted by any endpoint.
    """
    return secrets.token_urlsafe(48)
