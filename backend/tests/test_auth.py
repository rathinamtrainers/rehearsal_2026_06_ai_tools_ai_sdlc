"""End-to-end tests for the register/login slice against the frontend contract."""

from __future__ import annotations

from app.tokens import decode_access_token

VALID = {"name": "Priya Nair", "email": "priya@learnflow.io", "password": "Str0ng!pass"}


def _register(client, **overrides):
    return client.post("/auth/register", json={**VALID, **overrides})


def _login(client, **overrides):
    body = {"email": VALID["email"], "password": VALID["password"], **overrides}
    return client.post("/auth/login", json=body)


# ---- register -------------------------------------------------------------

def test_register_success(client):
    r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "ACTIVE"
    assert "message" in body


def test_register_duplicate_returns_409(client):
    _register(client)
    r = _register(client)
    assert r.status_code == 409
    assert r.json()["detail"] == "An account with this email already exists."


def test_register_duplicate_is_case_insensitive(client):
    _register(client)
    r = _register(client, email="PRIYA@LEARNFLOW.IO")
    assert r.status_code == 409


def test_register_weak_password_returns_422(client):
    r = _register(client, password="weak")
    assert r.status_code == 422


# ---- login ----------------------------------------------------------------

def test_login_success_returns_token_pair(client):
    _register(client)
    r = _login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]

    claims = decode_access_token(body["access_token"])
    assert claims["role"] == "learner"
    for required in ("sub", "role", "iat", "exp", "jti"):
        assert required in claims


def test_login_wrong_password_returns_401(client):
    _register(client)
    r = _login(client, password="Wr0ng!pass")
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password."


def test_login_unknown_email_returns_401(client):
    r = client.post("/auth/login", json={"email": "nobody@learnflow.io", "password": "Whatever1!"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password."


def test_login_lockout_after_five_failures_returns_429(client):
    _register(client)
    for _ in range(5):
        assert _login(client, password="Wr0ng!pass").status_code == 401
    # Account is now locked: even the correct password is refused with 429.
    r = _login(client)
    assert r.status_code == 429
    assert "Retry-After" in r.headers
    assert r.json()["detail"] == "Account temporarily locked. Try again in 15 minutes."


# ---- protected route (bearer dependency) ----------------------------------

def test_me_requires_bearer_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user_with_token(client):
    _register(client)
    token = _login(client).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == VALID["email"]
