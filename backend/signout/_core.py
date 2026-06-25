"""
_core.py — all utilities bundled for standalone use.
No imports from other project packages. Copy this folder and use it anywhere.

pip install:
  fastapi uvicorn sqlalchemy[asyncio] asyncpg alembic
  pydantic pydantic-settings python-jose[cryptography] bcrypt
  redis httpx aiosmtplib pyotp qrcode[pil]
"""
from __future__ import annotations

import hashlib
import hmac
import io
import json
import logging
import re
import secrets
import string
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from functools import lru_cache
from typing import Annotated, Any
from urllib.parse import urlencode

import aiosmtplib
import bcrypt
import httpx
import pyotp
import qrcode
import qrcode.image.svg
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import (
    AuditLog, MFABackupCode, Permission, Role, RolePermission,
    Session, Tenant, Token, TokenType, User, UserProfile, UserRole,
)

# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class AuthError(Exception):
    code: str = "AUTH_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class InvalidTokenError(AuthError):
    code = "INVALID_TOKEN"


class TokenExpiredError(AuthError):
    code = "TOKEN_EXPIRED"


class InvalidCredentialsError(AuthError):
    code = "INVALID_CREDENTIALS"


class AccountLockedError(AuthError):
    code = "ACCOUNT_LOCKED"

    def __init__(self, message: str, locked_until: str | None = None) -> None:
        super().__init__(message)
        self.locked_until = locked_until


class EmailNotVerifiedError(AuthError):
    code = "EMAIL_NOT_VERIFIED"


class MFARequiredError(AuthError):
    code = "MFA_REQUIRED"

    def __init__(self, mfa_session_token: str) -> None:
        super().__init__("MFA verification required")
        self.mfa_session_token = mfa_session_token


class InsufficientPermissionsError(AuthError):
    code = "INSUFFICIENT_PERMISSIONS"


class RateLimitExceededError(AuthError):
    code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TenantNotFoundError(AuthError):
    code = "TENANT_NOT_FOUND"


class UserNotFoundError(AuthError):
    code = "USER_NOT_FOUND"


class DuplicateEmailError(AuthError):
    code = "DUPLICATE_EMAIL"


class WeakPasswordError(AuthError):
    code = "WEAK_PASSWORD"


class OAuthError(AuthError):
    code = "OAUTH_ERROR"


class MFAError(AuthError):
    code = "MFA_ERROR"


# ─────────────────────────────────────────────────────────────────────────────
# Settings  (reads from .env in the module folder or environment variables)
# ─────────────────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required
    DATABASE_URL: str
    REDIS_URL: str
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    SECRET_KEY: str

    # Token lifetimes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # MFA
    MFA_ISSUER: str = "AuthModule"

    # OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    AUTH0_DOMAIN: str | None = None
    AUTH0_CLIENT_ID: str | None = None
    AUTH0_CLIENT_SECRET: str | None = None

    # Email (SMTP)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "noreply@auth.local"
    SMTP_USE_TLS: bool = False

    # HaveIBeenPwned
    HIBP_API_KEY: str | None = None
    HIBP_CHECK_ENABLED: bool = True

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True

    # DB pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @property
    def private_key(self) -> str:
        return self.JWT_PRIVATE_KEY.replace("\\n", "\n")

    @property
    def public_key(self) -> str:
        return self.JWT_PUBLIC_KEY.replace("\\n", "\n")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────

def _build_engine():
    s = get_settings()
    url = s.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return create_async_engine(
        url, pool_pre_ping=True,
        pool_size=s.DB_POOL_SIZE, max_overflow=s.DB_MAX_OVERFLOW,
    )


_engine = _build_engine()
AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─────────────────────────────────────────────────────────────────────────────
# Redis
# ─────────────────────────────────────────────────────────────────────────────

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _redis_pool


# ─────────────────────────────────────────────────────────────────────────────
# Token Service
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TokenClaims:
    sub: str
    jti: str
    tenant_id: str
    roles: list[str]
    permissions: list[str]
    exp: datetime
    iss: str
    aud: str


class TokenService:
    ALGORITHM = "RS256"

    def __init__(
        self,
        private_key: str,
        public_key: str,
        secret_key: str,
        issuer: str = "auth-module",
        audience: str = "auth-module-clients",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 30,
        redis_client: Any | None = None,
    ) -> None:
        self._private_key = private_key
        self._public_key = public_key
        self._secret_key = secret_key.encode()
        self.issuer = issuer
        self.audience = audience
        self.access_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_expire = timedelta(days=refresh_token_expire_days)
        self._redis = redis_client

    def generate_access_token(
        self, user_id: str, tenant_id: str, roles: list[str], permissions: list[str]
    ) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": now + self.access_expire,
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": permissions,
        }
        return jwt.encode(payload, self._private_key, algorithm=self.ALGORITHM)

    async def verify_access_token(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token, self._public_key, algorithms=[self.ALGORITHM],
                audience=self.audience, issuer=self.issuer,
            )
        except JWTError as exc:
            msg = str(exc).lower()
            if "expired" in msg:
                raise TokenExpiredError("Access token has expired") from exc
            raise InvalidTokenError(f"Invalid access token: {exc}") from exc
        jti = payload.get("jti", "")
        if await self._is_blacklisted(jti):
            raise InvalidTokenError("Token has been revoked")
        return TokenClaims(
            sub=payload["sub"],
            jti=jti,
            tenant_id=payload["tenant_id"],
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iss=payload["iss"],
            aud=payload["aud"] if isinstance(payload["aud"], str) else payload["aud"][0],
        )

    def generate_refresh_token(self) -> tuple[str, str]:
        raw = secrets.token_urlsafe(48)
        hashed = bcrypt.hashpw(raw.encode(), bcrypt.gensalt(rounds=12)).decode()
        return raw, hashed

    def verify_refresh_token(self, raw_token: str, stored_hash: str) -> bool:
        return bcrypt.checkpw(raw_token.encode(), stored_hash.encode())

    async def revoke_token(self, jti: str, ttl_seconds: int = 900) -> None:
        if self._redis:
            await self._redis.setex(f"blacklist:{jti}", ttl_seconds, "1")

    async def _is_blacklisted(self, jti: str) -> bool:
        if not self._redis or not jti:
            return False
        return bool(await self._redis.exists(f"blacklist:{jti}"))

    async def generate_otp(self, user_id: str, purpose: str, ttl_seconds: int = 600) -> str:
        raw = secrets.randbelow(10**6)
        code = str(raw).zfill(6)
        key = f"otp:{purpose}:{user_id}"
        code_hash = hashlib.sha256(
            hmac.new(self._secret_key, code.encode(), hashlib.sha256).digest()
        ).hexdigest()
        if self._redis:
            await self._redis.setex(key, ttl_seconds, code_hash)
        return code

    async def verify_otp(self, user_id: str, code: str, purpose: str) -> bool:
        key = f"otp:{purpose}:{user_id}"
        if not self._redis:
            return False
        stored_hash = await self._redis.get(key)
        if not stored_hash:
            return False
        expected = hashlib.sha256(
            hmac.new(self._secret_key, code.encode(), hashlib.sha256).digest()
        ).hexdigest()
        stored = stored_hash if isinstance(stored_hash, str) else stored_hash.decode()
        if hmac.compare_digest(expected, stored):
            await self._redis.delete(key)
            return True
        return False

    def generate_signed_token(self, user_id: str, purpose: str, ttl_hours: int = 24) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "iss": self.issuer,
            "purpose": purpose,
            "iat": now,
            "exp": now + timedelta(hours=ttl_hours),
        }
        return jwt.encode(payload, self._private_key, algorithm=self.ALGORITHM)

    async def verify_signed_token(self, token: str, purpose: str) -> str:
        try:
            payload = jwt.decode(
                token, self._public_key, algorithms=[self.ALGORITHM],
                options={"verify_aud": False}, issuer=self.issuer,
            )
        except JWTError as exc:
            msg = str(exc).lower()
            if "expired" in msg:
                raise TokenExpiredError("Token has expired") from exc
            raise InvalidTokenError("Invalid token") from exc
        if payload.get("purpose") != purpose:
            raise InvalidTokenError("Token purpose mismatch")
        if await self._is_blacklisted(payload.get("jti", "")):
            raise InvalidTokenError("Token has already been used")
        return payload["sub"]

    def generate_reset_token(self, user_id: str) -> str:
        return self.generate_signed_token(user_id, purpose="password_reset", ttl_hours=24)

    def generate_email_verify_token(self, user_id: str) -> str:
        return self.generate_signed_token(user_id, purpose="email_verify", ttl_hours=48)

    def generate_mfa_session_token(self, user_id: str, tenant_id: str) -> str:
        return self.generate_signed_token(user_id, purpose=f"mfa_session:{tenant_id}", ttl_hours=1)

    async def verify_mfa_session_token(self, token: str, tenant_id: str) -> str:
        return await self.verify_signed_token(token, purpose=f"mfa_session:{tenant_id}")

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        if self._redis:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            await self._redis.setex(
                f"revoke_all:{user_id}",
                int(self.access_expire.total_seconds()),
                str(now_ts),
            )

    async def is_user_tokens_revoked(self, user_id: str, issued_at: datetime) -> bool:
        if not self._redis:
            return False
        val = await self._redis.get(f"revoke_all:{user_id}")
        if not val:
            return False
        revoked_at = int(val if isinstance(val, str) else val.decode())
        return issued_at.timestamp() < revoked_at


# ─────────────────────────────────────────────────────────────────────────────
# Password Service
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    is_valid: bool
    score: int
    suggestions: list[str] = field(default_factory=list)
    pwned: bool = False


_UPPER = re.compile(r"[A-Z]")
_LOWER = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")
_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")


class PasswordService:
    BCRYPT_ROUNDS = 12
    HIBP_URL = "https://api.pwnedpasswords.com/range/{prefix}"

    def __init__(self, hibp_api_key: str | None = None) -> None:
        self._hibp_key = hibp_api_key

    def hash_password(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)).decode()

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def validate_password_strength(self, password: str) -> ValidationResult:
        suggestions: list[str] = []
        score = 0
        if len(password) < 8:
            suggestions.append("Use at least 8 characters")
        else:
            score += 1
        if not _UPPER.search(password):
            suggestions.append("Add at least one uppercase letter")
        else:
            score += 1
        if not _LOWER.search(password):
            suggestions.append("Add at least one lowercase letter")
        else:
            score += 1
        if not _DIGIT.search(password):
            suggestions.append("Add at least one digit")
        else:
            score += 1
        if not _SPECIAL_RE.search(password):
            suggestions.append("Add at least one special character (e.g. !@#$%)")
        else:
            score = min(score + 1, 4)
        if re.search(r"(.)\1{3,}", password):
            suggestions.append("Avoid repeated characters")
            score = max(score - 1, 0)
        return ValidationResult(
            is_valid=score >= 4 and len(password) >= 8,
            score=score,
            suggestions=suggestions,
        )

    async def is_pwned(self, password: str) -> bool:
        sha1 = hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]
        headers = {}
        if self._hibp_key:
            headers["hibp-api-key"] = self._hibp_key
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(self.HIBP_URL.format(prefix=prefix), headers=headers)
            resp.raise_for_status()
            for line in resp.text.splitlines():
                hash_suffix, _count = line.split(":")
                if hash_suffix == suffix:
                    return True
        except Exception:
            pass
        return False

    async def validate_with_hibp(self, password: str) -> ValidationResult:
        result = self.validate_password_strength(password)
        if result.is_valid:
            pwned = await self.is_pwned(password)
            if pwned:
                result = ValidationResult(
                    is_valid=False, score=result.score,
                    suggestions=["This password has appeared in a data breach. Choose a different one."],
                    pwned=True,
                )
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Email Sender
# ─────────────────────────────────────────────────────────────────────────────

class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._host = settings.SMTP_HOST
        self._port = settings.SMTP_PORT
        self._user = settings.SMTP_USER
        self._password = settings.SMTP_PASSWORD
        self._from = settings.SMTP_FROM
        self._use_tls = settings.SMTP_USE_TLS

    async def send_email(self, to: str, subject: str, body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["From"] = self._from
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            await aiosmtplib.send(
                msg,
                hostname=self._host,
                port=self._port,
                username=self._user or None,
                password=self._password or None,
                use_tls=self._use_tls,
                start_tls=False,
            )
        except Exception:
            logging.getLogger("auth.email").exception("Failed to send email to=%s", to)
            raise


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiter
# ─────────────────────────────────────────────────────────────────────────────

RATE_LIMIT_RULES: dict[str, dict[str, int]] = {
    "login":          {"limit": 5,  "window": 900},
    "signup":         {"limit": 3,  "window": 3600},
    "otp_send":       {"limit": 3,  "window": 600},
    "password_reset": {"limit": 3,  "window": 3600},
    "token_refresh":  {"limit": 10, "window": 60},
    "resend_verify":  {"limit": 1,  "window": 3600},
}


class RateLimiter:
    def __init__(self, redis_client: Any, enabled: bool = True) -> None:
        self._redis = redis_client
        self._enabled = enabled

    async def check(self, rule_name: str, identifier: str) -> None:
        if not self._enabled:
            return
        rule = RATE_LIMIT_RULES.get(rule_name)
        if not rule:
            raise ValueError(f"Unknown rate limit rule: {rule_name}")
        key = f"rl:{rule_name}:{identifier}"
        now = time.time()
        window_start = now - rule["window"]
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, rule["window"] + 1)
            results = await pipe.execute()
        current_count = results[1]
        if current_count >= rule["limit"]:
            await self._redis.zrem(key, str(now))
            oldest = await self._redis.zrange(key, 0, 0, withscores=True)
            reset_after = int(rule["window"] - (now - oldest[0][1])) if oldest else rule["window"]
            raise RateLimitExceededError(
                f"Too many {rule_name} attempts. Try again in {reset_after} seconds.",
                retry_after=reset_after,
            )


# ─────────────────────────────────────────────────────────────────────────────
# Lockout Service
# ─────────────────────────────────────────────────────────────────────────────

LOCKOUT_TIERS = [
    (5,  15),
    (10, 60),
    (20, 1440),
]


class LockoutService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def check_lockout(self, user_id: str) -> None:
        result = await self._db.execute(
            select(User.locked_until, User.failed_login_attempts, User.is_active)
            .where(User.id == uuid.UUID(user_id))
        )
        row = result.one_or_none()
        if not row:
            return
        locked_until, _attempts, is_active = row
        if not is_active:
            raise AccountLockedError("Account is disabled")
        if locked_until and locked_until > datetime.now(timezone.utc):
            raise AccountLockedError(
                f"Account locked until {locked_until.isoformat()}",
                locked_until=locked_until.isoformat(),
            )

    async def record_failed_attempt(self, user_id: str) -> None:
        result = await self._db.execute(
            select(User.failed_login_attempts).where(User.id == uuid.UUID(user_id))
        )
        row = result.one_or_none()
        if not row:
            return
        new_count = row[0] + 1
        lock_until: datetime | None = None
        now = datetime.now(timezone.utc)
        for min_failures, duration_minutes in reversed(LOCKOUT_TIERS):
            if new_count >= min_failures:
                lock_until = now + timedelta(minutes=duration_minutes)
                break
        await self._db.execute(
            update(User)
            .where(User.id == uuid.UUID(user_id))
            .values(failed_login_attempts=new_count, locked_until=lock_until)
        )
        await self._db.flush()

    async def reset_failed_attempts(self, user_id: str) -> None:
        await self._db.execute(
            update(User)
            .where(User.id == uuid.UUID(user_id))
            .values(failed_login_attempts=0, locked_until=None)
        )
        await self._db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# Audit Logger
# ─────────────────────────────────────────────────────────────────────────────

class EventType(str, Enum):
    USER_SIGNUP               = "USER_SIGNUP"
    USER_LOGIN_SUCCESS        = "USER_LOGIN_SUCCESS"
    USER_LOGIN_FAILED         = "USER_LOGIN_FAILED"
    USER_LOGOUT               = "USER_LOGOUT"
    PASSWORD_RESET_REQUESTED  = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED  = "PASSWORD_RESET_COMPLETED"
    PASSWORD_CHANGED          = "PASSWORD_CHANGED"
    EMAIL_VERIFIED            = "EMAIL_VERIFIED"
    MFA_ENABLED               = "MFA_ENABLED"
    MFA_DISABLED              = "MFA_DISABLED"
    MFA_VERIFIED              = "MFA_VERIFIED"
    MFA_FAILED                = "MFA_FAILED"
    TOKEN_REFRESHED           = "TOKEN_REFRESHED"
    TOKEN_REVOKED             = "TOKEN_REVOKED"
    ROLE_ASSIGNED             = "ROLE_ASSIGNED"
    ROLE_REVOKED              = "ROLE_REVOKED"
    ACCOUNT_LOCKED            = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED          = "ACCOUNT_UNLOCKED"
    OAUTH_LOGIN               = "OAUTH_LOGIN"
    SUSPICIOUS_ACTIVITY       = "SUSPICIOUS_ACTIVITY"


@dataclass
class RequestContext:
    ip_address: str | None = None
    user_agent: str | None = None
    device_fingerprint: str | None = None
    geo_country: str | None = None
    geo_city: str | None = None
    is_new_device: bool = False
    is_new_location: bool = False
    is_off_hours: bool = False


_RISK_BASE: dict[str, float] = {
    EventType.USER_LOGIN_FAILED:       0.3,
    EventType.PASSWORD_RESET_REQUESTED: 0.2,
    EventType.ACCOUNT_LOCKED:          0.7,
    EventType.SUSPICIOUS_ACTIVITY:     0.9,
    EventType.MFA_FAILED:              0.4,
    EventType.USER_LOGIN_SUCCESS:      0.0,
    EventType.USER_SIGNUP:             0.1,
    EventType.OAUTH_LOGIN:             0.05,
}


class AuditLogger:
    def __init__(self, db_session_factory: Any | None = None) -> None:
        self._session_factory = db_session_factory

    def calculate_risk_score(self, event_type: str, context: RequestContext) -> float:
        score = _RISK_BASE.get(event_type, 0.05)
        if context.is_new_device:
            score += 0.15
        if context.is_new_location:
            score += 0.1
        if context.is_off_hours:
            score += 0.05
        return round(min(score, 1.0), 3)

    async def log_event(
        self,
        event_type: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        request_context: RequestContext | None = None,
    ) -> None:
        ctx = request_context or RequestContext()
        risk = self.calculate_risk_score(event_type, ctx)
        structured = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "ip_address": ctx.ip_address,
            "user_agent": ctx.user_agent,
            "risk_score": risk,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _log = logging.getLogger("auth.audit")
        (_log.warning if risk >= 0.5 else _log.info)(json.dumps(structured))
        if self._session_factory:
            async with self._session_factory() as db:
                db.add(AuditLog(
                    tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
                    user_id=uuid.UUID(user_id) if user_id else None,
                    event_type=event_type,
                    event_data_json=metadata or {},
                    ip_address=ctx.ip_address,
                    user_agent=ctx.user_agent,
                    risk_score=risk,
                ))
                await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# MFA Service
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TOTPSetupResult:
    secret: str
    qr_code_uri: str
    qr_code_svg: str
    backup_codes: list[str]


class MFAService:
    TOTP_DIGITS = 6
    TOTP_INTERVAL = 30
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8
    OTP_TTL_SECONDS = 600

    def __init__(
        self,
        issuer: str = "AuthModule",
        redis_client: Any | None = None,
        notification_sender: Any | None = None,
    ) -> None:
        self._issuer = issuer
        self._redis = redis_client
        self._sender = notification_sender

    def setup_totp(self, user_id: str, user_email: str) -> tuple[TOTPSetupResult, list[str]]:
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, digits=self.TOTP_DIGITS, interval=self.TOTP_INTERVAL)
        uri = totp.provisioning_uri(name=user_email, issuer_name=self._issuer)
        img = qrcode.make(uri, image_factory=qrcode.image.svg.SvgImage)
        buf = io.BytesIO()
        img.save(buf)
        svg = buf.getvalue().decode()
        raw_codes, hashed_codes = self._generate_backup_codes()
        return TOTPSetupResult(secret=secret, qr_code_uri=uri, qr_code_svg=svg, backup_codes=raw_codes), hashed_codes

    def verify_totp(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret, digits=self.TOTP_DIGITS, interval=self.TOTP_INTERVAL)
        return totp.verify(code, valid_window=1)

    def _generate_backup_codes(self) -> tuple[list[str], list[str]]:
        alphabet = string.ascii_uppercase + string.digits
        raw_codes: list[str] = []
        hashed_codes: list[str] = []
        for _ in range(self.BACKUP_CODE_COUNT):
            code = "".join(secrets.choice(alphabet) for _ in range(self.BACKUP_CODE_LENGTH))
            hashed_codes.append(bcrypt.hashpw(code.encode(), bcrypt.gensalt(rounds=12)).decode())
            raw_codes.append(code)
        return raw_codes, hashed_codes

    def verify_backup_code(self, code: str, stored_hashes: list[str]) -> int | None:
        for idx, stored in enumerate(stored_hashes):
            if bcrypt.checkpw(code.encode(), stored.encode()):
                return idx
        return None

    def hash_backup_codes(self, raw_codes: list[str]) -> list[str]:
        return [bcrypt.hashpw(c.encode(), bcrypt.gensalt(rounds=12)).decode() for c in raw_codes]

    async def send_email_otp(self, user_id: str, email: str, purpose: str = "login") -> None:
        if not self._sender:
            raise MFAError("Email sender not configured")
        code = str(secrets.randbelow(10**6)).zfill(6)
        if self._redis:
            code_hash = bcrypt.hashpw(code.encode(), bcrypt.gensalt(rounds=6)).decode()
            await self._redis.setex(f"email_otp:{purpose}:{user_id}", self.OTP_TTL_SECONDS, code_hash)
        await self._sender.send_email(
            to=email, subject="Your verification code",
            body=f"Your code is: {code}\n\nIt expires in 10 minutes.",
        )

    async def verify_email_otp(self, user_id: str, code: str, purpose: str = "login") -> bool:
        key = f"email_otp:{purpose}:{user_id}"
        if not self._redis:
            return False
        stored = await self._redis.get(key)
        if not stored:
            return False
        stored_str = stored if isinstance(stored, str) else stored.decode()
        if bcrypt.checkpw(code.encode(), stored_str.encode()):
            await self._redis.delete(key)
            return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
# RBAC Engine
# ─────────────────────────────────────────────────────────────────────────────

class RBACEngine:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user_permissions(self, user_id: str, tenant_id: str) -> set[str]:
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(UserRole).where(
                UserRole.user_id == uuid.UUID(user_id),
                UserRole.tenant_id == uuid.UUID(tenant_id),
                (UserRole.expires_at == None) | (UserRole.expires_at > now),  # noqa: E711
            )
        )
        all_permissions: set[str] = set()
        for ur in result.scalars().all():
            all_permissions |= await self._resolve_role_permissions(ur.role_id)
        return all_permissions

    async def _resolve_role_permissions(
        self, role_id: uuid.UUID, _visited: set[uuid.UUID] | None = None
    ) -> set[str]:
        if _visited is None:
            _visited = set()
        if role_id in _visited:
            return set()
        _visited.add(role_id)
        result = await self._db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            return set()
        perm_result = await self._db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        perms = {p.name for p in perm_result.scalars().all()}
        if role.parent_role_id:
            perms |= await self._resolve_role_permissions(role.parent_role_id, _visited)
        return perms

    async def check_permission(self, user_id: str, permission: str, tenant_id: str) -> bool:
        perms = await self.get_user_permissions(user_id, tenant_id)
        if "*:*" in perms:
            return True
        resource, _action = permission.split(":", 1)
        return permission in perms or f"{resource}:*" in perms

    async def require_permission(self, user_id: str, permission: str, tenant_id: str) -> None:
        if not await self.check_permission(user_id, permission, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "INSUFFICIENT_PERMISSIONS", "message": f"Permission '{permission}' required"},
            )

    async def assign_role(
        self, user_id: str, role_name: str, tenant_id: str,
        assigned_by: str | None = None, expires_at: datetime | None = None,
    ) -> None:
        result = await self._db.execute(
            select(Role).where(
                Role.name == role_name,
                (Role.tenant_id == uuid.UUID(tenant_id)) | (Role.tenant_id == None),  # noqa: E711
            ).order_by(Role.tenant_id.nulls_last())
        )
        role = result.scalars().first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        existing = await self._db.execute(
            select(UserRole).where(
                UserRole.user_id == uuid.UUID(user_id),
                UserRole.role_id == role.id,
                UserRole.tenant_id == uuid.UUID(tenant_id),
            )
        )
        if existing.scalar_one_or_none():
            return
        self._db.add(UserRole(
            user_id=uuid.UUID(user_id), role_id=role.id, tenant_id=uuid.UUID(tenant_id),
            assigned_by=uuid.UUID(assigned_by) if assigned_by else None, expires_at=expires_at,
        ))
        await self._db.flush()

    async def revoke_role(self, user_id: str, role_name: str, tenant_id: str) -> None:
        result = await self._db.execute(
            select(Role).where(
                Role.name == role_name,
                (Role.tenant_id == uuid.UUID(tenant_id)) | (Role.tenant_id == None),  # noqa: E711
            ).order_by(Role.tenant_id.nulls_last())
        )
        role = result.scalars().first()
        if not role:
            return
        result = await self._db.execute(
            select(UserRole).where(
                UserRole.user_id == uuid.UUID(user_id),
                UserRole.role_id == role.id,
                UserRole.tenant_id == uuid.UUID(tenant_id),
            )
        )
        ur = result.scalar_one_or_none()
        if ur:
            await self._db.delete(ur)
            await self._db.flush()

    async def create_role(
        self, name: str, permissions: list[str],
        parent_role_name: str | None = None,
        tenant_id: str | None = None,
        description: str | None = None,
    ) -> Role:
        parent_id = None
        if parent_role_name:
            result = await self._db.execute(select(Role).where(Role.name == parent_role_name))
            parent = result.scalar_one_or_none()
            if parent:
                parent_id = parent.id
        role = Role(
            name=name, description=description,
            tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
            parent_role_id=parent_id,
        )
        self._db.add(role)
        await self._db.flush()
        for perm_name in permissions:
            result = await self._db.execute(select(Permission).where(Permission.name == perm_name))
            perm = result.scalar_one_or_none()
            if perm:
                self._db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        await self._db.flush()
        return role


# ─────────────────────────────────────────────────────────────────────────────
# OAuth Providers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OAuthTokens:
    access_token: str
    id_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = ""


@dataclass
class OAuthUserInfo:
    provider_user_id: str
    email: str
    email_verified: bool
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    raw: dict[str, Any] | None = None


class OAuthProvider(ABC):
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def get_authorization_url(self, state: str, redirect_uri: str) -> str: ...

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokens: ...

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo: ...


class GoogleOAuthProvider(OAuthProvider):
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._client_id = config["client_id"]
        self._client_secret = config["client_secret"]

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        return f"{self.AUTH_URL}?{urlencode({'client_id': self._client_id, 'redirect_uri': redirect_uri, 'response_type': 'code', 'scope': 'openid email profile', 'state': state, 'access_type': 'offline', 'prompt': 'consent'})}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokens:
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.TOKEN_URL, data={
                "code": code, "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": redirect_uri, "grant_type": "authorization_code",
            })
        if resp.status_code != 200:
            raise OAuthError(f"Token exchange failed: {resp.text}")
        d = resp.json()
        return OAuthTokens(access_token=d["access_token"], id_token=d.get("id_token"),
                           refresh_token=d.get("refresh_token"), expires_in=d.get("expires_in", 3600),
                           scope=d.get("scope", ""))

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if resp.status_code != 200:
            raise OAuthError(f"User info fetch failed: {resp.text}")
        d = resp.json()
        return OAuthUserInfo(provider_user_id=d["sub"], email=d["email"],
                             email_verified=d.get("email_verified", False),
                             first_name=d.get("given_name"), last_name=d.get("family_name"),
                             avatar_url=d.get("picture"), raw=d)


class Auth0Provider(OAuthProvider):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._domain = config["domain"]
        self._client_id = config["client_id"]
        self._client_secret = config["client_secret"]
        self._base = f"https://{self._domain}"

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        return f"{self._base}/authorize?{urlencode({'client_id': self._client_id, 'redirect_uri': redirect_uri, 'response_type': 'code', 'scope': 'openid email profile', 'state': state})}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokens:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self._base}/oauth/token", json={
                "grant_type": "authorization_code", "client_id": self._client_id,
                "client_secret": self._client_secret, "code": code, "redirect_uri": redirect_uri,
            })
        if resp.status_code != 200:
            raise OAuthError(f"Auth0 token exchange failed: {resp.text}")
        d = resp.json()
        return OAuthTokens(access_token=d["access_token"], id_token=d.get("id_token"),
                           expires_in=d.get("expires_in", 86400))

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._base}/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        if resp.status_code != 200:
            raise OAuthError(f"Auth0 user info failed: {resp.text}")
        d = resp.json()
        parts = d.get("name", "").split(" ", 1)
        return OAuthUserInfo(provider_user_id=d["sub"], email=d.get("email", ""),
                             email_verified=d.get("email_verified", False),
                             first_name=d.get("given_name", parts[0] if parts else None),
                             last_name=d.get("family_name", parts[1] if len(parts) > 1 else None),
                             avatar_url=d.get("picture"), raw=d)


class OAuthProviderRegistry:
    def __init__(self) -> None:
        self._instances: dict[str, OAuthProvider] = {}

    def configure(self, provider_type: str, config: dict[str, Any]) -> None:
        cls = {"google": GoogleOAuthProvider, "auth0": Auth0Provider}.get(provider_type)
        if not cls:
            raise OAuthError(f"Unknown provider: {provider_type}")
        self._instances[provider_type] = cls(config)

    def get(self, provider_type: str) -> OAuthProvider:
        p = self._instances.get(provider_type)
        if not p:
            raise OAuthError(f"Provider '{provider_type}' not configured")
        return p

    def generate_state(self, value: str, redis_client: Any) -> str:
        state = secrets.token_urlsafe(32)
        redis_client.setex(f"oauth_state:{state}", 600, value)
        return state

    def verify_state(self, state: str, redis_client: Any) -> str:
        val = redis_client.get(f"oauth_state:{state}")
        if not val:
            raise OAuthError("Invalid or expired OAuth state")
        redis_client.delete(f"oauth_state:{state}")
        return val if isinstance(val, str) else val.decode()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Dependencies  (wire these with Depends())
# ─────────────────────────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def get_token_service(redis: Any = Depends(get_redis)) -> TokenService:
    s = get_settings()
    return TokenService(
        private_key=s.private_key, public_key=s.public_key, secret_key=s.SECRET_KEY,
        access_token_expire_minutes=s.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=s.REFRESH_TOKEN_EXPIRE_DAYS,
        redis_client=redis,
    )


def get_password_service() -> PasswordService:
    return PasswordService(hibp_api_key=get_settings().HIBP_API_KEY)


def get_email_sender() -> SmtpEmailSender:
    return SmtpEmailSender(get_settings())


def get_rate_limiter(redis: Any = Depends(get_redis)) -> RateLimiter:
    return RateLimiter(redis_client=redis, enabled=get_settings().RATE_LIMIT_ENABLED)


def get_lockout_service(db: AsyncSession = Depends(get_db)) -> LockoutService:
    return LockoutService(db=db)


def get_audit_logger() -> AuditLogger:
    return AuditLogger(db_session_factory=AsyncSessionLocal)


def get_rbac(db: AsyncSession = Depends(get_db)) -> RBACEngine:
    return RBACEngine(db=db)


def get_mfa_service(redis: Any = Depends(get_redis)) -> MFAService:
    s = get_settings()
    return MFAService(issuer=s.MFA_ISSUER, redis_client=redis, notification_sender=SmtpEmailSender(s))


def get_oauth_registry() -> OAuthProviderRegistry:
    s = get_settings()
    registry = OAuthProviderRegistry()
    if s.GOOGLE_CLIENT_ID and s.GOOGLE_CLIENT_SECRET:
        registry.configure("google", {"client_id": s.GOOGLE_CLIENT_ID, "client_secret": s.GOOGLE_CLIENT_SECRET})
    if s.AUTH0_DOMAIN and s.AUTH0_CLIENT_ID and s.AUTH0_CLIENT_SECRET:
        registry.configure("auth0", {"domain": s.AUTH0_DOMAIN, "client_id": s.AUTH0_CLIENT_ID, "client_secret": s.AUTH0_CLIENT_SECRET})
    return registry


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: AsyncSession = Depends(get_db),
    token_svc: TokenService = Depends(get_token_service),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Authorization header required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = await token_svc.verify_access_token(credentials.credentials)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Access token has expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(claims.sub), User.deleted_at == None)  # noqa: E711
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "User not found or inactive"},
        )
    user._claims = claims  # type: ignore[attr-defined]
    return user
