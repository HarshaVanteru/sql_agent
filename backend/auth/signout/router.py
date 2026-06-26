"""Signout router — POST /auth/logout."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .._core import (
    AuditLogger,
    RequestContext,
    TokenService,
    User,
    get_audit_logger,
    get_current_user,
    get_db,
    get_token_service,
)
from .schemas import LogoutRequest, MessageResponse
from .service import signout

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/logout", response_model=MessageResponse)
async def logout_route(
    body: LogoutRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    token_svc: Annotated[TokenService, Depends(get_token_service)],
    audit: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> MessageResponse:
    """Revoke the current session. Pass all_devices=true to sign out everywhere."""
    ctx = RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return await signout(body, db, current_user, token_svc, audit, ctx)
