"""Business logic for signing out (single or all devices)."""
from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from .._core import AuditLogger, EventType, RequestContext, TokenService
from ..models import Session, User
from .schemas import LogoutRequest, MessageResponse


async def signout(
    body: LogoutRequest,
    db: AsyncSession,
    current_user: User,
    token_svc: TokenService,
    audit: AuditLogger,
    request_context: RequestContext,
) -> MessageResponse:
    claims = getattr(current_user, "_claims", None)
    if claims:
        await token_svc.revoke_token(claims.jti)

    if body.all_devices:
        await db.execute(
            update(Session)
            .where(Session.user_id == current_user.id)
            .values(is_active=False)
        )
        await token_svc.revoke_all_user_tokens(str(current_user.id))
    else:
        await db.execute(
            update(Session)
            .where(
                Session.user_id == current_user.id,
                Session.ip_address == request_context.ip_address,
                Session.is_active == True,  # noqa: E712
            )
            .values(is_active=False)
        )

    await audit.log_event(
        EventType.USER_LOGOUT,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        request_context=request_context,
    )
    return MessageResponse(message="Logged out successfully")
