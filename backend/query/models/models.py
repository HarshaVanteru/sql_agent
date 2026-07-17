"""Database models for conversation history."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.auth.models import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    database_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("databases.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # "user" or "assistant".
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    # The human-readable text: the user's question, or the agent's reply as the
    # user saw it. Empty for an assistant turn that answered purely with data.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Assistant turns only: the SQL the agent ran and a snapshot of its result
    # ({"columns", "rows", "row_count"}), so a reloaded conversation shows what
    # the user actually got without re-running the query. Null for user turns
    # and for replies that needed no query.
    sql_query: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
