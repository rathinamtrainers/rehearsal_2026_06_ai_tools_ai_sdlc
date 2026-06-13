"""The OAuth2 bearer dependency that protects routes.

``oauth2_scheme`` extracts ``Authorization: Bearer <token>``; ``get_current_user``
verifies the JWT and loads the user. The ``tokenUrl`` is nominal — it only labels
the scheme in the OpenAPI docs. Login itself accepts a JSON body (the React client
posts JSON), not the OAuth2 password form.
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, UserStatus
from .tokens import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=True)

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        claims = decode_access_token(token)
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _credentials_error

    user = db.get(User, user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise _credentials_error

    # Stale token after a password reset (token_version bumped) -> reject (EC-AUTH-JWT-03).
    if claims.get("tv") != user.token_version:
        raise _credentials_error

    return user
