"""Pydantic request/response models, with auth complexity validation.

Every model carries a ``json_schema_extra`` example so the generated OpenAPI
spec (``/openapi.json``) and the Swagger UI at ``/docs`` show realistic request
and response payloads rather than empty placeholders.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_SPECIAL = re.compile(r"[^A-Za-z0-9]")


def validate_password_complexity(value: str) -> str:
    """Enforce: >= 8 chars, 1 uppercase, 1 digit, 1 special (EC-AUTH-REG-04/05)."""
    errors: list[str] = []
    if len(value) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", value):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", value):
        errors.append("Password must contain at least one digit.")
    if not _SPECIAL.search(value):
        errors.append("Password must contain at least one special character.")
    if errors:
        # All failing rules reported together (not one-at-a-time probing).
        raise ValueError(" ".join(errors))
    return value


class RegisterRequest(BaseModel):
    """Payload for ``POST /auth/register`` — a new account's name, email, and password."""

    name: str = Field(min_length=1, max_length=255, description="Display name; 1–255 characters.")
    email: EmailStr = Field(description="Email address; normalised to lowercase and used as the login identifier.")
    # Cap at 72: bcrypt silently truncates input beyond 72 bytes, and hashing an
    # arbitrarily long string still costs the full work factor — an unbounded
    # field is a CPU-exhaustion (DoS) vector. (PR review High #4)
    password: str = Field(
        max_length=72,
        description="8+ chars with 1 uppercase, 1 digit, and 1 special char. Capped at 72 bytes (bcrypt limit).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Priya Sharma", "email": "priya@example.com", "password": "Password1!"}
        }
    )

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        return validate_password_complexity(v)


class LoginRequest(BaseModel):
    """Payload for ``POST /auth/login`` — email plus password."""

    email: EmailStr = Field(description="The email the account was registered with (case-insensitive).")
    # Same bcrypt 72-byte cap as registration — bounds work done per login attempt.
    password: str = Field(max_length=72, description="The account password. Capped at 72 bytes (bcrypt limit).")

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "priya@example.com", "password": "Password1!"}}
    )


class PasswordResetRequest(BaseModel):
    """Payload for ``POST /auth/password-reset/request`` — the email to send a reset link to."""

    email: EmailStr = Field(description="Email to send a reset link to (identical response whether or not it exists).")

    model_config = ConfigDict(json_schema_extra={"example": {"email": "priya@example.com"}})


class TokenResponse(BaseModel):
    """Successful-login response: a short-lived access token and a long-lived refresh token."""

    access_token: str = Field(description="Signed JWT for the Authorization: Bearer header; expires in ~15 min.")
    refresh_token: str = Field(description="Opaque token to obtain a new access token; only its hash is stored.")
    token_type: str = Field(default="bearer", description="Always 'bearer'.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI...",
                "refresh_token": "k3sN1q...redacted...9bYp",
                "token_type": "bearer",
            }
        }
    )


class MessageResponse(BaseModel):
    """A generic human-readable status message (used by register and password-reset)."""

    message: str = Field(description="A human-readable status message.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Account created. You can now log in."}}
    )


class ErrorResponse(BaseModel):
    """The body returned for 4xx auth errors (FastAPI's ``HTTPException`` shape)."""

    detail: str = Field(description="A human-readable explanation of why the request was rejected.")

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Invalid email or password."}})


class UserResponse(BaseModel):
    """The current authenticated user's public profile (``GET /auth/me``)."""

    id: str = Field(description="Server-generated UUID for the user.")
    email: EmailStr = Field(description="The user's email address.")
    name: str = Field(description="The user's display name.")
    role: str = Field(description="Authorization role: 'learner', 'instructor', or 'admin'.")
    status: str = Field(description="Account status: 'ACTIVE', 'PENDING_VERIFICATION', 'LOCKED', or 'DEACTIVATED'.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "5f1d2c8e-9b3a-4c7d-8e2f-1a2b3c4d5e6f",
                "email": "priya@example.com",
                "name": "Priya Sharma",
                "role": "learner",
                "status": "ACTIVE",
            }
        }
    )
