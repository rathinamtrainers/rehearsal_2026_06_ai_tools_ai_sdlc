"""Auth-router edge cases: inactive registration, non-active login states,
expired-lock recovery, and the enumeration-safe password-reset endpoint.

These exercise the branches the happy-path suite in test_auth.py doesn't reach.
"""
from __future__ import annotations

from datetime import timedelta

from conftest import VALID_PASSWORD, login, register

from app.config import settings
from app.models import User, UserStatus, utcnow


def _get_user(db, email: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    assert user is not None
    return user


def test_register_inactive_returns_verify_message(client, monkeypatch):
    # REGISTER_ACTIVE=false => account is PENDING_VERIFICATION and the message
    # tells the user to verify their email (auth.py:94).
    monkeypatch.setattr(settings, "register_active", False)
    resp = register(client, "pending@example.com")
    assert resp.status_code == 201
    assert "verify" in resp.json()["message"].lower()


def test_login_pending_verification_forbidden(client, monkeypatch):
    # A PENDING_VERIFICATION account with the *right* password is still 403 (auth.py:119).
    monkeypatch.setattr(settings, "register_active", False)
    register(client, "pending2@example.com")
    resp = login(client, "pending2@example.com")
    assert resp.status_code == 403
    assert "verified" in resp.json()["detail"].lower()


def test_login_deactivated_forbidden(client, db):
    # A DEACTIVATED account is rejected with 403 even with the right password (auth.py:124).
    register(client, "deactivated@example.com")
    user = _get_user(db, "deactivated@example.com")
    user.status = UserStatus.DEACTIVATED
    db.commit()

    resp = login(client, "deactivated@example.com")
    assert resp.status_code == 403
    assert "deactivated" in resp.json()["detail"].lower()


def test_login_clears_expired_lock(client, db):
    # Status LOCKED but the lock window already elapsed: a correct login should
    # succeed AND flip the account back to ACTIVE (auth.py:133-134).
    register(client, "waslocked@example.com")
    user = _get_user(db, "waslocked@example.com")
    user.status = UserStatus.LOCKED
    user.failed_attempts = 5
    user.locked_until = utcnow() - timedelta(minutes=1)  # already expired
    db.commit()

    resp = login(client, "waslocked@example.com", password=VALID_PASSWORD)
    assert resp.status_code == 200
    assert resp.json()["access_token"]

    refreshed = _get_user(db, "waslocked@example.com")
    db.refresh(refreshed)
    assert refreshed.status == UserStatus.ACTIVE
    assert refreshed.failed_attempts == 0
    assert refreshed.locked_until is None


def test_password_reset_request_is_enumeration_safe(client):
    # Identical 202 whether or not the account exists (auth.py:145-146).
    register(client, "exists@example.com")

    existing = client.post("/auth/password-reset/request", json={"email": "exists@example.com"})
    missing = client.post("/auth/password-reset/request", json={"email": "nobody@example.com"})

    assert existing.status_code == 202
    assert missing.status_code == 202
    assert existing.json() == missing.json()
