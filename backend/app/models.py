"""ORM models for the LearnFlow auth module."""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_aware(dt: datetime | None) -> datetime | None:
    """Treat naive datetimes (e.g. read back from SQLite) as UTC."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


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

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=32),
        default=UserStatus.PENDING_VERIFICATION,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=16),
        default=UserRole.learner,
        nullable=False,
    )

    # Brute-force lockout (named / per-user).
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Bumped to bulk-invalidate every outstanding JWT for this user.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    """Opaque refresh token — only the hash is stored (rotation-ready)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class QuestionType(str, enum.Enum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passing_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    questions: Mapped[list[Question]] = relationship(
        "Question", back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False)
    question_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, native_enum=False, length=32), nullable=False
    )

    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correct_option_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_true: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="questions")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, native_enum=False, length=32),
        default=AttemptStatus.IN_PROGRESS,
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
