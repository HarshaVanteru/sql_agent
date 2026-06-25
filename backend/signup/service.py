"""Business logic for user sign-up."""
from __future__ import annotations

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ._core import AuditLogger, EventType, PasswordService, RateLimiter, RequestContext, SmtpEmailSender, TokenService
from .models import Tenant, User, UserProfile
from .schemas import SignupRequest, SignupResponse


async def signup(
    body: SignupRequest,
    db: AsyncSession,
    pwd_svc: PasswordService,
    token_svc: TokenService,
    rate_limiter: RateLimiter,
    audit: AuditLogger,
    settings: object,
    background_tasks: BackgroundTasks,
    request_context: RequestContext,
) -> SignupResponse:
    await rate_limiter.check("signup", request_context.ip_address or "unknown")

    validation = await pwd_svc.validate_with_hibp(body.password)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "WEAK_PASSWORD",
                "message": (
                    "Password must be at least 8 characters and contain one uppercase "
                    "letter, one number, and one special character (!@#$%^&*)."
                ),
                "details": {"suggestions": validation.suggestions, "score": validation.score},
            },
        )

    tenant_id = (await db.execute(select(Tenant.id).limit(1))).scalar_one_or_none()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT",
                "message": "No tenant exists. Run scripts/seed.py or create a tenant first.",
            },
        )

    existing = await db.execute(
        select(User).where(
            User.email == body.email,
            User.tenant_id == tenant_id,
            User.deleted_at == None,  # noqa: E711
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_EXISTS", "message": "Check your email to verify your account"},
        )

    pwd_hash = pwd_svc.hash_password(body.password)
    user = User(tenant_id=tenant_id, email=body.email, password_hash=pwd_hash, is_verified=False)
    db.add(user)
    await db.flush()

    profile = UserProfile(user_id=user.id, first_name=body.first_name, last_name=body.last_name)
    db.add(profile)

    verify_token = token_svc.generate_email_verify_token(str(user.id))
    sender = SmtpEmailSender(settings)  # type: ignore[arg-type]
    background_tasks.add_task(_send_verification_email, sender, user.email, verify_token)

    await audit.log_event(
        EventType.USER_SIGNUP,
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        metadata={"email": user.email},
        request_context=request_context,
    )

    return SignupResponse(user_id=str(user.id), message="Check your email to verify your account")


async def _send_verification_email(sender: SmtpEmailSender, email: str, token: str) -> None:
    body = (
        f"Welcome! Please verify your email address by using the token below.\n\n"
        f"Token:\n{token}\n\n"
        f"This link expires in 48 hours. If you did not sign up, ignore this email."
    )
    await sender.send_email(to=email, subject="Verify your email address", body=body)
