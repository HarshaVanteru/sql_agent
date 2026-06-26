"""Pydantic schemas for the signout module."""
from __future__ import annotations

from pydantic import BaseModel


class LogoutRequest(BaseModel):
    all_devices: bool = False


class MessageResponse(BaseModel):
    message: str
