"""Signin router — POST /auth/login."""
from __future__ import annotations

from typing import Annotated, Union

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .._core import (
    AuditLogger,
    LockoutService,
    PasswordService,
    RateLimiter,
    RequestContext,
    TokenService,
    get_audit_logger,
    get_db,
    get_lockout_service,
    get_password_service,
    get_rate_limiter,
    get_token_service,
)
from .schemas import LoginRequest, LoginResponse, MFARequiredResponse, RefreshTokenRequest, RefreshTokenResponse
from .service import signin, refresh_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login_route(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    pwd_svc: Annotated[PasswordService, Depends(get_password_service)],
    token_svc: Annotated[TokenService, Depends(get_token_service)],
    lockout_svc: Annotated[LockoutService, Depends(get_lockout_service)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    audit: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> Union[LoginResponse, MFARequiredResponse]:
    """Authenticate with email + password. Returns tokens or an MFA challenge."""
    ctx = RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return await signin(body, db, pwd_svc, token_svc, lockout_svc, rate_limiter, audit, ctx)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_route(
    body: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    token_svc: Annotated[TokenService, Depends(get_token_service)],
) -> RefreshTokenResponse:
    """Generate a new access token from a refresh token."""
    return await refresh_access_token(body, db, token_svc)
