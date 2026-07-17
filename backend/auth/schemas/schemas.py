"""Pydantic schemas for authentication.

Shapes match what the frontend already sends and expects, so AuthContext keeps
working unchanged.
"""
from pydantic import BaseModel, EmailStr, Field

from backend.auth.security import MIN_PASSWORD_LENGTH


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=72)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class SignupResponse(BaseModel):
    user_id: str
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class MeResponse(BaseModel):
    user: UserResponse
