"""Pydantic schemas for the signin module."""
from __future__ import annotations

import re

from pydantic import BaseModel, field_validator


def validate_email(v: str) -> str:
    v = v.strip().lower()
    if len(v) > 255:
        raise ValueError("Email must be at most 255 characters.")
    if not re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", v):
        raise ValueError("Enter a valid email address.")
    return v


class DeviceInfo(BaseModel):
    fingerprint: str | None = None
    user_agent: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
    device_info: DeviceInfo | None = None

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, v: str) -> str:
        return validate_email(v)

    @field_validator("password", mode="before")
    @classmethod
    def _password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password is required.")
        return v


class UserSummary(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    roles: list[str]
    permissions: list[str]
    is_verified: bool
    mfa_enabled: bool


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
    user: UserSummary


class MFARequiredResponse(BaseModel):
    mfa_required: bool = True
    mfa_session_token: str
    available_methods: list[str]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
