"""Query and conversation shapes."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.validators import RequiredText


class NaturalLanguageQueryRequest(BaseModel):
    question: RequiredText("Question", 4000)  # type: ignore[valid-type]
    # Absent starts a new conversation; present continues one, which is what
    # lets "now only the ones in London" refine the previous question.
    conversation_id: str | None = None


class NaturalLanguageQueryResponse(BaseModel):
    query: str | None = None
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    row_count: int = 0
    conversation_id: str | None = None
    message: str | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sql_query: str | None = None
    result: dict[str, Any] | None = None
    created_at: datetime


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]
    total: int


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]
