"""Test fixtures: an isolated temp-file SQLite DB and a TestClient per test."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models  # noqa: F401  (register tables on Base.metadata)
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def _engine(tmp_path):
    """A fresh temp-file SQLite engine per test; always disposed on teardown."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def _SessionLocal(_engine):
    return sessionmaker(
        bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


@pytest.fixture()
def client(_SessionLocal) -> Iterator[TestClient]:
    def override_get_db():
        db = _SessionLocal()
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


@pytest.fixture()
def db(_SessionLocal) -> Iterator[Session]:
    """A direct session on the same DB the client uses, for arranging state the
    API has no endpoint for yet (e.g. bumping token_version)."""
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
