"""ORM models for the LearnFlow auth domain.

Only the ``users`` table is built this iteration (per the approved plan). The
columns mirror the BRD data model (§3.6) — including the ones this slice doesn't
yet exercise (``token_version`` for future bulk-JWT revocation) so the schema is
forward-compatible with refresh-token and password-reset iterations.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, SmallInteger, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class UserStatus(str, enum.Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    DEACTIVATED = "DEACTIVATED"


class UserRole(str, enum.Enum):
    learner = "learner"
    instructor = "instructor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # native_enum=False -> portable VARCHAR + CHECK constraint (SQLite & Postgres).
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=32), nullable=False, default=UserStatus.ACTIVE
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=16), nullable=False, default=UserRole.learner
    )

    failed_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_version: Mapped[int] = mapped_column(nullable=False, default=0)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User {self.email} status={self.status.value}>"
