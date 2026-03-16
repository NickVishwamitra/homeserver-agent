from datetime import UTC, datetime
from importlib import import_module
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.integrations.listenbrainz import MusicBrainzMetadataLookupResult
from app.integrations.listenbrainz.models import ListenBrainzToolResult

ChatRole = Literal["system", "user", "assistant"]
StructuredToolResult = MusicBrainzMetadataLookupResult | ListenBrainzToolResult


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


class ChatMessage(BaseModel):
    """A single chat message stored for a conversation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: ChatRole
    content: str = Field(min_length=1)
    structured_data: list[StructuredToolResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ChatStreamRequest(BaseModel):
    """Payload containing the next user message to stream a reply for."""

    content: str = Field(min_length=1, max_length=4000)


class ConversationResponse(BaseModel):
    """A full conversation snapshot returned to the frontend."""

    id: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage]


class GeneratedChatReply(BaseModel):
    """Internal reply model with assistant text and tool results."""

    text: str
    structured_data: list[StructuredToolResult]


class ChatReplyResponse(BaseModel):
    """The assistant reply plus the updated conversation state."""

    assistant_message: ChatMessage
    conversation: ConversationResponse


class ConversationTtlResponse(BaseModel):
    """Debug information about a conversation expiration state."""

    conversation_id: str
    configured_ttl_seconds: int
    ttl_seconds_remaining: int
    exists: bool


_listenbrainz_module = import_module("app.integrations.listenbrainz")
_types_namespace = {
    "StructuredToolResult": StructuredToolResult,
}
ChatMessage.model_rebuild(_types_namespace=_types_namespace)
GeneratedChatReply.model_rebuild(_types_namespace=_types_namespace)
