import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Self
from uuid import uuid4

from strands.session.file_session_manager import FileSessionManager

from app.schemas import ChatMessage, ConversationResponse

if TYPE_CHECKING:
    from app.schemas import StructuredToolResult


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


@dataclass
class ConversationState:
    """Mutable chat state for a single conversation."""

    id: str
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    messages: list[ChatMessage] = field(default_factory=list)


class _ConversationLock:
    """Async lock wrapper used to serialize writes per conversation."""

    def __init__(self, lock: asyncio.Lock, timeout_seconds: int) -> None:
        self._lock = lock
        self._timeout_seconds = timeout_seconds
        self._acquired = False

    async def __aenter__(self) -> Self:
        await asyncio.wait_for(self._lock.acquire(), timeout=self._timeout_seconds)
        self._acquired = True
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._acquired and self._lock.locked():
            self._lock.release()


class FileSessionChatStore:
    """Store chat conversations with Strands FileSessionManager and TTL."""

    def __init__(
        self,
        session_storage_dir: str,
        ttl_seconds: int = 3600,
        lock_timeout_seconds: int = 120,
    ) -> None:
        """Initialize filesystem-backed chat session settings."""
        self._session_storage_dir = Path(session_storage_dir).resolve()
        self._session_storage_dir.mkdir(parents=True, exist_ok=True)
        self._ttl_seconds = ttl_seconds
        self._lock_timeout_seconds = lock_timeout_seconds
        self._locks: dict[str, asyncio.Lock] = {}

    async def close(self) -> None:
        """No-op close hook kept for parity with the app lifespan."""

    def conversation_lock(self, conversation_id: str) -> _ConversationLock:
        """Return an async lock that serializes writes for one conversation."""
        lock = self._locks.setdefault(conversation_id, asyncio.Lock())
        return _ConversationLock(
            lock=lock,
            timeout_seconds=self._lock_timeout_seconds,
        )

    def _session_path(self, conversation_id: str) -> Path:
        return self._session_storage_dir / f"session_{conversation_id}"

    def _conversation_file_path(self, conversation_id: str) -> Path:
        return self._session_path(conversation_id) / "conversation_state.json"

    def _session_manager(self, conversation_id: str) -> FileSessionManager:
        return FileSessionManager(
            session_id=conversation_id,
            storage_dir=str(self._session_storage_dir),
        )

    def _is_expired(self, conversation: ConversationState) -> bool:
        age_seconds = (utc_now() - conversation.updated_at).total_seconds()
        return age_seconds >= self._ttl_seconds

    async def _delete_conversation(self, conversation_id: str) -> None:
        session_path = self._session_path(conversation_id)
        if not session_path.exists():
            return
        session_manager = self._session_manager(conversation_id)
        session_manager.delete_session(conversation_id)

    async def get_conversation_ttl(self, conversation_id: str) -> int:
        """Return remaining TTL seconds, mirroring Redis-style missing semantics."""
        conversation = await self.get_conversation(conversation_id)
        if conversation is None:
            return -2

        age_seconds = int((utc_now() - conversation.updated_at).total_seconds())
        return max(0, self._ttl_seconds - age_seconds)

    def _to_response(self, conversation: ConversationState) -> ConversationResponse:
        return ConversationResponse(
            id=conversation.id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=list(conversation.messages),
        )

    async def _save_conversation(self, conversation: ConversationState) -> None:
        self._session_manager(conversation.id)
        payload = self._to_response(conversation).model_dump(mode="json")
        conversation_file = self._conversation_file_path(conversation.id)
        conversation_file.parent.mkdir(parents=True, exist_ok=True)
        conversation_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def create_conversation(
        self,
    ) -> ConversationResponse:
        """Create a new filesystem-backed conversation and return its snapshot."""
        conversation = ConversationState(
            id=str(uuid4()),
        )
        await self._save_conversation(conversation)
        return self._to_response(conversation)

    async def get_conversation(self, conversation_id: str) -> ConversationState | None:
        """Look up a conversation by id without refreshing its TTL."""
        conversation_file = self._conversation_file_path(conversation_id)
        if not conversation_file.exists():
            return None

        payload = conversation_file.read_text(encoding="utf-8")
        response = ConversationResponse.model_validate_json(payload)
        conversation = ConversationState(
            id=response.id,
            created_at=response.created_at,
            updated_at=response.updated_at,
            messages=list(response.messages),
        )

        if self._is_expired(conversation):
            await self._delete_conversation(conversation_id)
            return None

        return ConversationState(
            id=response.id,
            created_at=response.created_at,
            updated_at=response.updated_at,
            messages=list(response.messages),
        )

    def _touch(self, conversation: ConversationState) -> None:
        conversation.updated_at = utc_now()

    async def add_user_message(
        self,
        conversation: ConversationState,
        content: str,
    ) -> ChatMessage:
        """Append a user message and refresh the session TTL."""
        message = ChatMessage(role="user", content=content)
        conversation.messages.append(message)
        self._touch(conversation)
        await self._save_conversation(conversation)
        return message

    async def add_assistant_message(
        self,
        conversation: ConversationState,
        content: str,
        structured_data: list[StructuredToolResult] | None = None,
        message_id: str | None = None,
    ) -> ChatMessage:
        """Append an assistant message and refresh the session TTL."""
        message = ChatMessage(
            id=message_id or str(uuid4()),
            role="assistant",
            content=content,
            structured_data=structured_data or [],
        )
        conversation.messages.append(message)
        self._touch(conversation)
        await self._save_conversation(conversation)
        return message

    async def to_response(
        self,
        conversation: ConversationState,
    ) -> ConversationResponse:
        """Convert mutable state into the response model returned by the API."""
        return self._to_response(conversation)
