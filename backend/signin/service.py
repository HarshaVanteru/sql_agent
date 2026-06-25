"""Business logic for sign-in, including session creation shared by other modules."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Union

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ._core import (
    AuditLogger,
    EventType,
    LockoutService,
    PasswordService,
    RBACEngine,
    RateLimiter,
    RequestContext,
    TokenService,
)
from .models import Role, Session, User, UserRole
from .schemas import LoginRequest, LoginResponse, MFARequiredResponse, UserSummary


async def signin(
    body: LoginRequest,
    db: AsyncSession,
    pwd_svc: PasswordService,
    token_svc: TokenService,
    lockout_svc: LockoutService,
    rate_limiter: RateLimiter,
    audit: AuditLogger,
    request_context: RequestContext,
) -> Union[LoginResponse, MFARequiredResponse]:
    ip = request_context.ip_address or "unknown"
    await rate_limiter.check("login", ip)

    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(
            User.email == body.email,
            User.deleted_at == None,  # noqa: E711
        )
    )
    user = result.scalar_one_or_none()

    password_ok = (
        user is not None
        and user.password_hash is not None
        and pwd_svc.verify_password(body.password, user.password_hash)
    )

    if not user or not password_ok:
        if user:
            await lockout_svc.record_failed_attempt(str(user.id))
            await audit.log_event(
                EventType.USER_LOGIN_FAILED,
                tenant_id=str(user.tenant_id),
                user_id=str(user.id),
                request_context=request_context,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect"},
        )

    await lockout_svc.check_lockout(str(user.id))

    if user.mfa_enabled:
        mfa_token = token_svc.generate_mfa_session_token(str(user.id), str(user.tenant_id))
        return MFARequiredResponse(
            mfa_session_token=mfa_token,
            available_methods=["totp", "backup", "email_otp"],
        )

    return await create_session_response(user, db, token_svc, audit, request_context)


async def create_session_response(
    user: User,
    db: AsyncSession,
    token_svc: TokenService,
    audit: AuditLogger,
    ctx: RequestContext,
) -> LoginResponse:
    rbac = RBACEngine(db)
    permissions = await rbac.get_user_permissions(str(user.id), str(user.tenant_id))

    result = await db.execute(select(UserRole).where(UserRole.user_id == user.id))
    role_ids = [ur.role_id for ur in result.scalars().all()]
    roles: list[str] = []
    if role_ids:
        roles_result = await db.execute(select(Role).where(Role.id.in_(role_ids)))
        roles = [r.name for r in roles_result.scalars().all()]

    access_token = token_svc.generate_access_token(
        str(user.id), str(user.tenant_id), roles, list(permissions)
    )
    raw_refresh, refresh_hash = token_svc.generate_refresh_token()

    session = Session(
        user_id=user.id,
        tenant_id=user.tenant_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
        refresh_token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(session)

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            last_login_at=datetime.now(timezone.utc),
            failed_login_attempts=0,
            locked_until=None,
        )
    )

    await audit.log_event(
        EventType.USER_LOGIN_SUCCESS,
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        request_context=ctx,
    )

    profile = user.profile
    return LoginResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=UserSummary(
            id=str(user.id),
            email=user.email,
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
            roles=roles,
            permissions=list(permissions),
            is_verified=user.is_verified,
            mfa_enabled=user.mfa_enabled,
        ),
    )
