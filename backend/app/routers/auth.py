"""Auth endpoints for LearnFlow UC-1: register, login, password-reset request,
and current-user lookup.

This router is the public HTTP surface of the auth slice. Password hashing and
JWT issuing live in :mod:`app.security`; bearer-token validation lives in
:mod:`app.deps`. The endpoints here own the request/response contract the
frontend (``frontend/src/api/authClient.ts``) depends on, including the exact
status codes documented in the OpenAPI ``responses`` blocks below.
"""
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
    ErrorResponse,
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
    """Look up a user by email, case-insensitively (emails are stored lowercased)."""
    normalized = email.strip().lower()
    return db.query(User).filter(func.lower(User.email) == normalized).first()


def _is_locked(user: User) -> bool:
    """Return True while the user's brute-force lockout window is still in effect."""
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
    """Mint a JWT access token, persist a hashed refresh token, and return both."""
    access_token = create_access_token(user)
    raw_refresh, token_hash, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, token_type="bearer")


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    responses={
        status.HTTP_201_CREATED: {
            "model": MessageResponse,
            "description": "Account created. The message tells the user whether they can log in immediately "
            "(`REGISTER_ACTIVE=true`) or must verify their email first.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "An account with this email already exists.",
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation failed — e.g. malformed email, or a password that doesn't meet the "
            "complexity rules (8+ chars, 1 uppercase, 1 digit, 1 special).",
        },
    },
)
def register(payload: RegisterRequest, db: DbSession) -> MessageResponse:
    """Create a new learner account.

    The email is normalised to lowercase and must be unique (a duplicate returns
    `409`). The password is validated for complexity (`422` on failure) and stored
    as a bcrypt hash — never in plaintext. Depending on `REGISTER_ACTIVE`, the new
    account is either immediately `ACTIVE` or `PENDING_VERIFICATION`; the returned
    message reflects which. No token is issued here — the client logs in separately.
    """
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


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and obtain access + refresh tokens",
    responses={
        status.HTTP_200_OK: {
            "model": TokenResponse,
            "description": "Authenticated. Returns a short-lived access token and a long-lived refresh token.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Invalid email or password. The same generic error is returned for an unknown "
            "email and a wrong password, to avoid account enumeration.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "The credentials are correct but the account cannot log in: email not yet "
            "verified (`PENDING_VERIFICATION`) or the account is `DEACTIVATED`.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Account temporarily locked after too many failed attempts "
            "(5 failures / 10 min → locked for 15 min).",
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation failed — e.g. a malformed email address.",
        },
    },
)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    """Authenticate a user and issue tokens.

    On success returns an access token (JWT, ~15 min) plus a refresh token, and
    clears any prior failed-attempt/lockout state. Failure modes are deliberately
    distinct: a wrong password or unknown email both return a generic `401`
    (enumeration-safe, constant-time); 5 failures inside the rolling window lock
    the account and subsequent attempts return `429`; a correct password on a
    `PENDING_VERIFICATION` or `DEACTIVATED` account returns `403`.
    """
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


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password-reset link",
)
def password_reset_request(payload: PasswordResetRequest, db: DbSession) -> MessageResponse:
    """Begin the password-reset flow for an email address.

    Always returns `202` with the same message whether or not the email maps to an
    account, so the endpoint can't be used to discover which emails are registered.
    NOTE: actual email dispatch and reset-token persistence are out of UC-1 scope —
    this is the enumeration-safe entry point the full flow will build on.
    """
    # Enumeration-safe: identical 202 whether or not the account exists (AC-AUTH-10).
    # NOTE: real email dispatch + token persistence are out of UC-1's register/login scope.
    _ = _get_user_by_email(db, payload.email)
    return MessageResponse(message="If an account exists for this email, a reset link has been sent.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
    responses={
        status.HTTP_200_OK: {"model": UserResponse, "description": "The authenticated user's profile."},
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Missing, malformed, expired, or invalidated bearer token.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "The token is valid but the account is no longer active.",
        },
    },
)
def me(current_user: CurrentUser) -> UserResponse:
    """Return the profile of the user identified by the `Authorization: Bearer` token.

    The token is validated by the `get_current_user` dependency (signature, expiry,
    `token_version`, and account status) before this handler runs.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        status=current_user.status.value,
    )
