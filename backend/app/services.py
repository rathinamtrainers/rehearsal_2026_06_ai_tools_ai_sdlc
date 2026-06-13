"""Auth domain logic: registration and credential authentication with lockout.

Kept out of the router so the rules are unit-testable and reusable. HTTP error
details use the exact, security-reviewed strings from the BRD and the frontend
contract (e.g. the 409 ``detail`` is read verbatim by the React client).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import User, UserRole, UserStatus
from .passwords import hash_password, verify_dummy, verify_password
from .schemas import RegisterRequest

INVALID_CREDENTIALS = "Invalid email or password."
ACCOUNT_LOCKED = "Account temporarily locked. Try again in 15 minutes."
DUPLICATE_EMAIL = "An account with this email already exists."
ACCOUNT_DEACTIVATED = "This account has been deactivated. Please contact support."
EMAIL_UNVERIFIED = (
    "Your email address has not been verified. "
    "Please check your inbox or request a new verification link."
)


def _aware(dt: datetime | None) -> datetime | None:
    """Normalise to UTC-aware. SQLite returns naive datetimes; Postgres returns aware."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_CREDENTIALS,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def register_user(db: Session, data: RegisterRequest) -> User:
    """Create a new learner. Duplicate email -> 409 (AC-AUTH-02).

    NOTE (dev deviation): the account is created ACTIVE so register->login works
    end-to-end without an email provider. Per AC-AUTH-01 this should be
    PENDING_VERIFICATION until the verification link is clicked; flip the default
    once email sending exists.
    """
    if get_user_by_email(db, data.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_EMAIL)

    user = User(
        email=data.email.strip().lower(),
        password_hash=hash_password(data.password),
        full_name=data.name.strip(),
        status=UserStatus.ACTIVE,
        role=UserRole.learner,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Verify credentials, applying lockout. Returns the user or raises HTTPException.

    See the plan's decision flow. Responses are deliberately non-specific (same 401
    for unknown-email and wrong-password) and timing-normalised against a dummy hash
    to avoid account enumeration (AC-AUTH-05 / FR-09).
    """
    now = datetime.now(timezone.utc)
    user = get_user_by_email(db, email)

    if user is None:
        verify_dummy()  # constant-time: cost a bcrypt verify even with no user
        raise _invalid_credentials()

    locked_until = _aware(user.locked_until)

    # Already locked -> 429, skip the password check entirely (EC-AUTH-LGN-02).
    if locked_until is not None and locked_until > now:
        retry_after = max(1, int((locked_until - now).total_seconds()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ACCOUNT_LOCKED,
            headers={"Retry-After": str(retry_after)},
        )

    # Lock has expired -> clear it before evaluating the new attempt.
    if locked_until is not None and locked_until <= now:
        user.failed_attempts = 0
        user.locked_until = None
        if user.status == UserStatus.LOCKED:
            user.status = UserStatus.ACTIVE

    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        # Crossing the threshold locks the account but still returns the standard
        # 401 — never tell the attacker they hit the limit (EC-AUTH-LGN-04).
        if user.failed_attempts >= settings.max_failed_attempts:
            user.status = UserStatus.LOCKED
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
        db.commit()
        raise _invalid_credentials()

    # Password correct — gate on account status (EC-AUTH-LGN-01 / LGN-03).
    if user.status == UserStatus.DEACTIVATED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ACCOUNT_DEACTIVATED)
    if user.status == UserStatus.PENDING_VERIFICATION:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=EMAIL_UNVERIFIED)

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()
    db.refresh(user)
    return user
