"""Business logic for authentication."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import Session, User
from backend.auth.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_expiry,
    verify_password,
)
from backend.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    SignupRequest,
    SignupResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)


def _as_utc(value: datetime) -> datetime:
    """Treat a stored timestamp as UTC.

    Neither MySQL's DATETIME nor SQLite keeps tzinfo, so values read back are
    naive and cannot be compared against an aware `now` without this.
    """
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
    )


async def signup(body: SignupRequest, db: AsyncSession) -> SignupResponse:
    """Register an account."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_EMAIL", "message": "An account with that email already exists"},
        )

    try:
        password_hash = hash_password(body.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "WEAK_PASSWORD", "message": str(e)},
        )

    user = User(
        email=body.email,
        password_hash=password_hash,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    db.add(user)
    await db.commit()

    logger.info(f"Account created: {user.id}")
    return SignupResponse(user_id=user.id, message="Account created. You can now log in.")


async def login(body: LoginRequest, db: AsyncSession) -> LoginResponse:
    """Authenticate and issue an access token plus a refresh session."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Verify against a dummy hash when the account is missing so that a failed
    # lookup and a wrong password take the same time.
    if not user:
        verify_password(body.password, "$2b$12$" + "." * 53)
        raise _invalid_credentials()

    if not verify_password(body.password, user.password_hash):
        logger.info(f"Failed login for user {user.id}")
        raise _invalid_credentials()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "This account is disabled"},
        )

    raw_refresh, refresh_hash = generate_refresh_token()
    db.add(Session(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        expires_at=refresh_expiry(),
    ))
    await db.commit()

    logger.info(f"Login: {user.id}")
    return LoginResponse(
        access_token=create_access_token(user.id),
        refresh_token=raw_refresh,
        user=UserResponse.model_validate(user),
    )


async def refresh(body: RefreshRequest, db: AsyncSession) -> RefreshResponse:
    """Exchange a refresh token for a new access token."""
    result = await db.execute(
        select(Session).where(Session.refresh_token_hash == hash_refresh_token(body.refresh_token))
    )
    session = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not session or session.revoked_at or _as_utc(session.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Refresh token is invalid or expired"},
        )

    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "User not found or inactive"},
        )

    return RefreshResponse(access_token=create_access_token(user.id))


async def logout(refresh_token: str | None, user_id: str, db: AsyncSession) -> dict:
    """Revoke a refresh session. Revokes every session for the user if no token given."""
    query = select(Session).where(Session.user_id == user_id, Session.revoked_at.is_(None))
    if refresh_token:
        query = query.where(Session.refresh_token_hash == hash_refresh_token(refresh_token))

    result = await db.execute(query)
    sessions = result.scalars().all()

    now = datetime.now(timezone.utc)
    for session in sessions:
        session.revoked_at = now
    await db.commit()

    logger.info(f"Logout: revoked {len(sessions)} session(s) for user {user_id}")
    return {"message": "Logged out"}
