"""Auth endpoints: register, login, password-reset request, and current user."""
from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import CurrentUser
from app.models import RefreshToken, User, UserRole, UserStatus, ensure_aware, utcnow
from app.schemas import (
    LoginRequest,
    MessageResponse,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    create_access_token,
    dummy_verify,
    generate_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]

INVALID_CREDENTIALS = "Invalid email or password."
DUPLICATE_EMAIL = "An account with this email already exists."
ACCOUNT_LOCKED = "Account temporarily locked. Try again in 15 minutes."


def _get_user_by_email(db: Session, email: str) -> User | None:
    normalized = email.strip().lower()
    return db.query(User).filter(func.lower(User.email) == normalized).first()


def _is_locked(user: User) -> bool:
    locked_until = ensure_aware(user.locked_until)
    return locked_until is not None and locked_until > utcnow()


def _register_failure(db: Session, user: User) -> None:
    """Increment the named-account failure counter, locking on threshold."""
    now = utcnow()
    window = timedelta(minutes=settings.lockout_window_minutes)
    last_failed_at = ensure_aware(user.last_failed_at)
    # Reset the counter if the previous failure is outside the rolling window.
    if last_failed_at is None or (now - last_failed_at) > window:
        user.failed_attempts = 0
    user.failed_attempts += 1
    user.last_failed_at = now
    if user.failed_attempts >= settings.lockout_max_attempts:
        user.locked_until = now + timedelta(minutes=settings.lockout_duration_minutes)
        user.status = UserStatus.LOCKED
    db.commit()


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(user)
    raw_refresh, token_hash, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, token_type="bearer")


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> MessageResponse:
    if _get_user_by_email(db, payload.email) is not None:
        # Duplicate email — enumeration trade-off is accepted here (AC-AUTH-02).
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_EMAIL)

    initial_status = UserStatus.ACTIVE if settings.register_active else UserStatus.PENDING_VERIFICATION
    user = User(
        email=payload.email.strip().lower(),
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        status=initial_status,
        role=UserRole.learner,
    )
    db.add(user)
    db.commit()

    if settings.register_active:
        message = "Account created. You can now log in."
    else:
        message = "Account created. Check your inbox to verify your email."
    return MessageResponse(message=message)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = _get_user_by_email(db, payload.email)

    # Unknown email — constant-time dummy verify, generic 401 (EC-AUTH-LGN-05).
    if user is None:
        dummy_verify(payload.password)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS)

    # Locked — skip password evaluation entirely (EC-AUTH-LGN-02).
    if _is_locked(user):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=ACCOUNT_LOCKED)

    # Wrong password — count the failure (may cross the lockout threshold).
    if not verify_password(payload.password, user.password_hash):
        _register_failure(db, user)
        # The crossing attempt still returns 401, not 429 (EC-AUTH-LGN-04).
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS)

    # Not yet verified (only reachable when REGISTER_ACTIVE=false) — EC-AUTH-LGN-01.
    if user.status == UserStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your email address has not been verified. Please check your inbox.",
        )
    if user.status == UserStatus.DEACTIVATED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support.",
        )

    # Success — clear lockout state, stamp login, issue tokens (AC-AUTH-04).
    user.failed_attempts = 0
    user.last_failed_at = None
    user.locked_until = None
    if user.status == UserStatus.LOCKED:
        user.status = UserStatus.ACTIVE
    user.last_login_at = utcnow()
    db.commit()

    return _issue_tokens(db, user)


@router.post("/password-reset/request", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def password_reset_request(payload: PasswordResetRequest, db: DbSession) -> MessageResponse:
    # Enumeration-safe: identical 202 whether or not the account exists (AC-AUTH-10).
    # NOTE: real email dispatch + token persistence are out of UC-1's register/login scope.
    _ = _get_user_by_email(db, payload.email)
    return MessageResponse(message="If an account exists for this email, a reset link has been sent.")


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        status=current_user.status.value,
    )
