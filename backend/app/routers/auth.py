"""/auth/* endpoints — register, login, and a protected /auth/me.

Shapes and status codes match ``frontend/src/api/auth.ts``:
  • register -> 201 {message, status}; duplicate -> 409
  • login    -> 200 {access_token, refresh_token, token_type}; bad creds -> 401; locked -> 429
``/auth/me`` exists to exercise the bearer dependency end-to-end.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, RegisterResponse, TokenPair, UserOut
from ..services import authenticate, register_user
from ..tokens import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    user = register_user(db, payload)
    return RegisterResponse(message="Account created. You can now log in.", status=user.status)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = authenticate(db, payload.email, payload.password)
    return TokenPair(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(),
        token_type="bearer",
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
