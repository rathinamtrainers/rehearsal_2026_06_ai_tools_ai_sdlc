"""Pydantic v2 request/response schemas — the wire contract with the React client.

Field names and shapes match ``frontend/src/api/auth.ts`` exactly: register takes
``{name, email, password}``; login returns ``{access_token, refresh_token,
token_type}``. The password validator enforces the same LearnFlow complexity rules
the frontend's ``scorePassword`` checks, so a weak password is rejected with 422
even if a client skips its own validation (defense in depth — EC-AUTH-REG-04/05).
"""

from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from .models import UserRole, UserStatus

_SPECIAL = re.compile(r"""[!@#$%^&*(),.?":{}|<>_\-\[\]\\/+=;'`~]""")


def validate_password_complexity(pw: str) -> str:
    """≥8 chars, 1 uppercase, 1 digit, 1 special — raise ValueError on the first miss."""
    if len(pw) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", pw):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", pw):
        raise ValueError("Password must contain at least one digit.")
    if not _SPECIAL.search(pw):
        raise ValueError("Password must contain at least one special character.")
    return pw


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    # bcrypt silently ignores bytes past 72, so without this cap any password
    # sharing the first 72 bytes of the registered one would authenticate —
    # a silent auth bypass. Cap the length; the complexity rules run after.
    password: str = Field(max_length=72)

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return validate_password_complexity(v)


class RegisterResponse(BaseModel):
    message: str
    status: UserStatus


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus

    model_config = {"from_attributes": True}
