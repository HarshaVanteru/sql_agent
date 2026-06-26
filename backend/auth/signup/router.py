"""Authentication router — signup, login, email verification."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .._core import (
    AuditLogger,
    PasswordService,
    RateLimiter,
    RequestContext,
    TokenService,
    get_audit_logger,
    get_db,
    get_password_service,
    get_rate_limiter,
    get_settings,
    get_token_service,
)
from .schemas import SignupRequest, SignupResponse, LoginRequest, LoginResponse, VerifyEmailRequest, ResendVerificationRequest
from .service import signup, login, verify_email, resend_verification

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup_route(
    body: SignupRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    pwd_svc: Annotated[PasswordService, Depends(get_password_service)],
    token_svc: Annotated[object, Depends(get_token_service)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    audit: Annotated[AuditLogger, Depends(get_audit_logger)],
    settings: Annotated[object, Depends(get_settings)],
) -> SignupResponse:
    """Register a new user account. Sends an email verification link."""
    ctx = RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return await signup(body, db, pwd_svc, token_svc, rate_limiter, audit, settings, background_tasks, ctx)


@router.post("/login", response_model=LoginResponse)
async def login_route(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    pwd_svc: Annotated[PasswordService, Depends(get_password_service)],
    token_svc: Annotated[object, Depends(get_token_service)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    audit: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> LoginResponse:
    """Sign in with email and password."""
    ctx = RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return await login(body, db, pwd_svc, token_svc, rate_limiter, audit, ctx)


@router.post("/verify-email", response_model=LoginResponse)
async def verify_email_route(
    body: VerifyEmailRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    token_svc: Annotated[object, Depends(get_token_service)],
    audit: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> LoginResponse:
    """Verify email with code."""
    ctx = RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return await verify_email(body, db, token_svc, audit, ctx)


@router.post("/resend-verification")
async def resend_verification_route(
    body: ResendVerificationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    token_svc: Annotated[object, Depends(get_token_service)],
    settings: Annotated[object, Depends(get_settings)],
) -> dict:
    """Resend email verification code."""
    ctx = RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return await resend_verification(body, db, token_svc, settings, background_tasks, ctx)
