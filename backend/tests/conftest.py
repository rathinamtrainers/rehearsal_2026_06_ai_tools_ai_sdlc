"""Pytest fixtures: a FastAPI TestClient backed by an isolated temp SQLite DB.

Each test gets its own throwaway database file and a `get_db` dependency
override, so tests never touch the real `learnflow.db` and never see each
other's rows. A `db` fixture exposes a Session on the *same* database so tests
can set up state (e.g. a DEACTIVATED user) the public API can't reach.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 — import registers the ORM tables on Base.metadata
from app.database import Base, get_db
from app.main import app

VALID_PASSWORD = "Password1!"  # meets the complexity rules: 8+, upper, digit, special


@pytest.fixture
def engine() -> Iterator[Engine]:
    # A fresh temp SQLite file per test => full isolation.
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="learnflow_test_")
    os.close(fd)
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        eng.dispose()
        os.remove(db_path)


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
def client(session_factory: sessionmaker) -> Iterator[TestClient]:
    def override_get_db() -> Iterator:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def db(session_factory: sessionmaker) -> Iterator[Session]:
    """A Session on the same DB the client uses, for direct state setup/asserts."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def register(client: TestClient, email: str, password: str = VALID_PASSWORD, name: str = "Test User"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password})


def login(client: TestClient, email: str, password: str = VALID_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})
