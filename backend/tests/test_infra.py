"""Infrastructure-level coverage: the /health probe and the real get_db generator."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def test_health_endpoint_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_db_yields_session_and_closes(monkeypatch):
    # Exercise the production get_db generator (database.py:23-27) against a
    # throwaway in-memory engine, so it both yields a Session and runs its
    # `finally: db.close()` on exhaustion.
    from app import database

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine))

    gen = database.get_db()
    session = next(gen)
    assert isinstance(session, Session)

    with pytest.raises(StopIteration):
        next(gen)  # triggers the finally/close branch
