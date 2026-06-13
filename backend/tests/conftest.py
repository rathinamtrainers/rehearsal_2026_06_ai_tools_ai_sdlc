"""Test fixtures: an isolated temp-file SQLite DB and a TestClient per test."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (register tables on Base.metadata)
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
