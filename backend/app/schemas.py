"""Pydantic request/response models, with auth complexity validation."""
from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

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
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        return validate_password_complexity(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    status: str
