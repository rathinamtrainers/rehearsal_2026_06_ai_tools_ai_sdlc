"""get_current_user / bearer-token validation branches (app/deps.py).

Each test forges a JWT signed with the app's own secret to drive /auth/me into
a specific failure branch that the normal login flow never produces.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from conftest import login, register

from app.config import settings
from app.models import User


def _make_token(**claims) -> str:
    """Sign an arbitrary claim set with the app's configured JWT secret/alg."""
    now = datetime.now(timezone.utc)
    payload = {"iat": now, "exp": now + timedelta(minutes=15), **claims}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_expired_token_unauthorized(client):
    # exp in the past => jwt.ExpiredSignatureError => 401 (deps.py:31-36).
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = jwt.encode(
        {"sub": "whoever", "token_version": 0, "iat": past, "exp": past},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/auth/me", headers=_auth(token))
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_me_token_missing_sub_unauthorized(client):
    # Valid signature but no "sub" claim => 401 (deps.py:41-42).
    token = _make_token(token_version=0)
    resp = client.get("/auth/me", headers=_auth(token))
    assert resp.status_code == 401


def test_me_token_unknown_user_unauthorized(client):
    # Well-formed token for a user id that isn't in the DB => 401 (deps.py:45-46).
    token = _make_token(sub="00000000-0000-0000-0000-000000000000", token_version=0)
    resp = client.get("/auth/me", headers=_auth(token))
    assert resp.status_code == 401


def test_me_token_version_mismatch_unauthorized(client, db):
    # Bumping token_version after issue invalidates the old token => 401 (deps.py:49-54).
    register(client, "rotated@example.com")
    token = login(client, "rotated@example.com").json()["access_token"]

    user = db.query(User).filter(User.email == "rotated@example.com").first()
    user.token_version += 1  # simulates a password reset / forced logout
    db.commit()

    resp = client.get("/auth/me", headers=_auth(token))
    assert resp.status_code == 401
    assert "invalidated" in resp.json()["detail"].lower()


def test_me_inactive_user_forbidden(client, db):
    # Valid, version-matching token but the account is no longer ACTIVE => 403 (deps.py:56-60).
    register(client, "frozen@example.com")
    token = login(client, "frozen@example.com").json()["access_token"]

    user = db.query(User).filter(User.email == "frozen@example.com").first()
    from app.models import UserStatus

    user.status = UserStatus.DEACTIVATED
    db.commit()

    resp = client.get("/auth/me", headers=_auth(token))
    assert resp.status_code == 403
    assert "not active" in resp.json()["detail"].lower()
