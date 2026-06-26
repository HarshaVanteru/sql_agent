"""Business logic for authentication."""
from __future__ import annotations

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from .._core import AuditLogger, EventType, PasswordService, RateLimiter, RequestContext, SmtpEmailSender, TokenService
from ..models import Tenant, User, UserProfile
from .schemas import SignupRequest, SignupResponse, LoginRequest, LoginResponse, UserResponse, VerifyEmailRequest, ResendVerificationRequest


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
    user = User(tenant_id=tenant_id, email=body.email, password_hash=pwd_hash, is_verified=True)
    db.add(user)
    await db.flush()

    profile = UserProfile(user_id=user.id, first_name=body.first_name, last_name=body.last_name)
    db.add(profile)
    await db.commit()

    await audit.log_event(
        EventType.USER_SIGNUP,
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        metadata={"email": user.email},
        request_context=request_context,
    )

    return SignupResponse(user_id=str(user.id), message="Account created successfully. Please login.")


async def _send_verification_email(sender: SmtpEmailSender, email: str, token: str) -> None:
    print(f"[EMAIL] Sending verification email to={email}")
    body = (
        f"Welcome! Please verify your email address by using the token below.\n\n"
        f"Token:\n{token}\n\n"
        f"This link expires in 48 hours. If you did not sign up, ignore this email."
    )
    await sender.send_email(to=email, subject="Verify your email address", body=body)
    print(f"[EMAIL] Verification email completed for={email}")


async def login(
    body: LoginRequest,
    db: AsyncSession,
    pwd_svc: PasswordService,
    token_svc: TokenService,
    rate_limiter: RateLimiter,
    audit: AuditLogger,
    request_context: RequestContext,
) -> LoginResponse:
    """Authenticate user with email and password."""
    await rate_limiter.check("login", request_context.ip_address or "unknown")

    tenant_id = (await db.execute(select(Tenant.id).limit(1))).scalar_one_or_none()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT",
                "message": "No tenant exists.",
            },
        )

    user = (
        await db.execute(
            select(User).where(
                User.email == body.email,
                User.tenant_id == tenant_id,
                User.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()

    if not user or not pwd_svc.verify_password(body.password, user.password_hash or ""):
        await audit.log_event(
            EventType.USER_LOGIN_FAILED,
            tenant_id=str(tenant_id),
            metadata={"email": body.email},
            request_context=request_context,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    if not user.is_verified:
        await audit.log_event(
            EventType.USER_LOGIN_FAILED,
            tenant_id=str(tenant_id),
            user_id=str(user.id),
            metadata={"email": user.email, "reason": "email_not_verified"},
            request_context=request_context,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "EMAIL_NOT_VERIFIED", "message": "Please verify your email first"},
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        await audit.log_event(
            EventType.ACCOUNT_LOCKED,
            tenant_id=str(tenant_id),
            user_id=str(user.id),
            metadata={"email": user.email},
            request_context=request_context,
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={"code": "ACCOUNT_LOCKED", "message": "Account is temporarily locked"},
        )

    # Reset failed login attempts on successful login
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(failed_login_attempts=0, last_login_at=datetime.now(timezone.utc))
    )
    await db.commit()

    access_token = token_svc.generate_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        roles=[],
        permissions=[],
    )

    await audit.log_event(
        EventType.USER_LOGIN_SUCCESS,
        tenant_id=str(tenant_id),
        user_id=str(user.id),
        metadata={"email": user.email},
        request_context=request_context,
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(id=str(user.id), email=user.email),
    )


async def verify_email(
    body: VerifyEmailRequest,
    db: AsyncSession,
    token_svc: TokenService,
    audit: AuditLogger,
    request_context: RequestContext,
) -> LoginResponse:
    """Verify email with verification code."""
    user = (
        await db.execute(select(User).where(User.id == body.user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    # Verify the code using token service
    is_valid = await token_svc.verify_otp(body.user_id, body.code, "email_verify")
    if not is_valid:
        await audit.log_event(
            EventType.SUSPICIOUS_ACTIVITY,
            tenant_id=str(user.tenant_id),
            user_id=str(user.id),
            metadata={"email": user.email, "reason": "invalid_verification_code"},
            request_context=request_context,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_CODE", "message": "Invalid or expired verification code"},
        )

    # Mark email as verified
    await db.execute(
        update(User).where(User.id == user.id).values(is_verified=True)
    )
    await db.commit()

    access_token = token_svc.generate_access_token(str(user.id))

    await audit.log_event(
        EventType.EMAIL_VERIFIED,
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        metadata={"email": user.email},
        request_context=request_context,
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(id=str(user.id), email=user.email),
    )


async def resend_verification(
    body: ResendVerificationRequest,
    db: AsyncSession,
    token_svc: TokenService,
    settings: object,
    background_tasks: BackgroundTasks,
    request_context: RequestContext,
) -> dict:
    """Resend email verification code."""
    tenant_id = (await db.execute(select(Tenant.id).limit(1))).scalar_one_or_none()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_TENANT", "message": "No tenant exists."},
        )

    user = (
        await db.execute(
            select(User).where(
                User.email == body.email,
                User.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()

    if not user:
        # Don't reveal whether email exists
        return {"message": "If email exists, verification code sent"}

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "ALREADY_VERIFIED", "message": "Email already verified"},
        )

    # Generate new verification code
    verify_token = token_svc.generate_email_verify_token(str(user.id))
    sender = SmtpEmailSender(settings)  # type: ignore[arg-type]

    background_tasks.add_task(_send_verification_email, sender, user.email, verify_token)

    return {"message": "Verification email sent"}
