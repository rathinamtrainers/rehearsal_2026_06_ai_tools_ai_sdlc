"""Auth dependencies — OAuth2 bearer extraction and current-user resolution."""
from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserStatus
from app.security import decode_access_token

# tokenUrl is documentation metadata for the OpenAPI "Authorize" button.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": 'Bearer realm="learnflow", error="invalid_token"'},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the authenticated :class:`User` from a bearer token, or raise.

    Decodes and verifies the JWT, then enforces, in order: a present ``sub``
    claim, an existing user, a matching ``token_version`` (so a password reset
    can bulk-invalidate old tokens), and an ``ACTIVE`` account status. Raises
    ``401`` for any token/identity problem and ``403`` for a valid token whose
    account is not active. Used as a FastAPI dependency via :data:`CurrentUser`.
    """
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please refresh your session.",
            headers={"WWW-Authenticate": 'Bearer realm="learnflow", error="token_expired"'},
        ) from exc
    except jwt.PyJWTError as exc:
        raise _UNAUTHORIZED from exc

    user_id = payload.get("sub")
    if not user_id:
        raise _UNAUTHORIZED

    user = db.get(User, user_id)
    if user is None:
        raise _UNAUTHORIZED

    # token_version mismatch => token invalidated by a password reset (EC-AUTH-JWT-03).
    if payload.get("token_version") != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has been invalidated. Please log in again.",
            headers={"WWW-Authenticate": 'Bearer realm="learnflow", error="invalid_token"'},
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
