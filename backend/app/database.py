"""SQLAlchemy 2.0 engine, session factory, declarative base, and the get_db dependency.

Sync SQLAlchemy keeps the code straightforward and runs identically on SQLite (dev)
and PostgreSQL (prod). The only dialect-specific touch is SQLite's
``check_same_thread`` flag, applied automatically when the URL is SQLite.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    # SQLite + a threaded dev server (uvicorn/TestClient) needs this; harmless elsewhere.
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model and by Alembic's autogenerate."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
