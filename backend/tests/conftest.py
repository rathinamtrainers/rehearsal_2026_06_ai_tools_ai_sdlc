"""Pytest fixtures: a FastAPI TestClient backed by an isolated temp SQLite DB.

Each test gets its own throwaway database file and a `get_db` dependency
override, so tests never touch the real `learnflow.db` and never see each
other's rows.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — import registers the ORM tables on Base.metadata
from app.database import Base, get_db
from app.main import app

VALID_PASSWORD = "Password1!"  # meets the complexity rules: 8+, upper, digit, special


@pytest.fixture
def client() -> Iterator[TestClient]:
    # A fresh temp SQLite file per test => full isolation.
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="learnflow_test_")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Iterator:
        db = TestingSessionLocal()
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
        engine.dispose()
        os.remove(db_path)


def register(client: TestClient, email: str, password: str = VALID_PASSWORD, name: str = "Test User"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password})


def login(client: TestClient, email: str, password: str = VALID_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})
