"""Database models for connection management."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.auth.models import Base

if TYPE_CHECKING:
    from backend.auth.models import User


class Database(Base):
    __tablename__ = "databases"
    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_databases_name_user"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    db_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # One-directional: auth owns User and should not need to know what else
    # references it. Deleting a user still cascades via the FK.
    user: Mapped[User] = relationship()
    credentials: Mapped[DatabaseCredential] = relationship(
        back_populates="database", cascade="all, delete-orphan", uselist=False
    )


class DatabaseCredential(Base):
    __tablename__ = "database_credentials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    database_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("databases.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    database_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    database: Mapped[Database] = relationship(back_populates="credentials")
