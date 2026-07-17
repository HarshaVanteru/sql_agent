"""Authentication router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.db import get_db
from backend.auth.models import User
from backend.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    SignupRequest,
    SignupResponse,
    UserResponse,
)
from backend.auth.service import login, logout, refresh, signup

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup_route(
    body: SignupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SignupResponse:
    """Register an account with an email and password."""
    return await signup(body, db)


@router.post("/login", response_model=LoginResponse)
async def login_route(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    """Authenticate and receive an access token and a refresh token."""
    return await login(body, db)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_route(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RefreshResponse:
    """Exchange a refresh token for a fresh access token."""
    return await refresh(body, db)


@router.post("/logout")
async def logout_route(
    body: LogoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Revoke the given refresh session, or all of this user's sessions."""
    return await logout(body.refresh_token, current_user.id, db)


@router.get("/me", response_model=MeResponse)
async def me_route(
    current_user: Annotated[User, Depends(get_current_user)],
) -> MeResponse:
    """Return the authenticated account."""
    return MeResponse(user=UserResponse.model_validate(current_user))
