"""Auth backend tests: register, login, /auth/me, and brute-force lockout.

Covers the happy path plus the core error cases called out in the PR review's
"zero tests" finding.
"""
from __future__ import annotations

from conftest import VALID_PASSWORD, login, register


def test_register_success(client):
    resp = register(client, "alice@example.com")
    assert resp.status_code == 201
    assert "message" in resp.json()


def test_register_duplicate_email_conflicts(client):
    register(client, "dupe@example.com")
    # Same email again (case-insensitive) => 409.
    resp = register(client, "DUPE@example.com")
    assert resp.status_code == 409


def test_register_weak_password_unprocessable(client):
    resp = register(client, "weak@example.com", password="weak")
    assert resp.status_code == 422


def test_login_success_returns_tokens(client):
    register(client, "bob@example.com")
    resp = login(client, "bob@example.com")
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password_unauthorized(client):
    register(client, "carol@example.com")
    resp = login(client, "carol@example.com", password="Wrongpass1!")
    assert resp.status_code == 401


def test_login_unknown_email_unauthorized(client):
    resp = login(client, "ghost@example.com")
    assert resp.status_code == 401


def test_me_with_bearer_returns_profile(client):
    register(client, "dave@example.com")
    token = login(client, "dave@example.com").json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "dave@example.com"


def test_me_without_bearer_unauthorized(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_garbage_token_unauthorized(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert resp.status_code == 401


def test_lockout_after_five_failures(client):
    """5 wrong passwords lock the account; the next attempt is rejected with 429.

    Per the implementation (EC-AUTH-LGN-04) the 5th/threshold-crossing attempt
    still returns 401 — the account is locked, so the *following* attempt (even
    with the right password) is what surfaces the 429.
    """
    register(client, "mallory@example.com")

    for _ in range(5):
        bad = login(client, "mallory@example.com", password="Wrongpass1!")
        assert bad.status_code == 401

    # Account is now locked: even the correct password is short-circuited to 429.
    locked = login(client, "mallory@example.com", password=VALID_PASSWORD)
    assert locked.status_code == 429
