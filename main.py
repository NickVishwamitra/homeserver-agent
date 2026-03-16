import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException

from agent import generate_chat_reply
from app.chat_service import FileSessionChatStore
from app.config import settings
from app.schemas import (
    ChatReplyResponse,
    ChatStreamRequest,
    ConversationResponse,
    ConversationTtlResponse,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown resources."""
    try:
        yield
    finally:
        await chat_store.close()


app = FastAPI(
    title="API and Agent for homeserver",
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "Analyzes failed GitLab merge request pipelines with AWS Bedrock via Strands "
        "using pipeline logs and git diffs."
    ),
)
chat_store = FileSessionChatStore(
    session_storage_dir=settings.chat_session_storage_dir,
    ttl_seconds=settings.chat_session_ttl_seconds,
    lock_timeout_seconds=settings.chat_conversation_lock_timeout_seconds,
)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    """Return a simple readiness response."""
    return {"status": "ok"}


@app.post("/api/chat/conversations/create", response_model=ConversationResponse)
async def create_conversation() -> ConversationResponse:
    """Create a new chat conversation."""
    return await chat_store.create_conversation()


@app.get(
    "/api/chat/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(conversation_id: str) -> ConversationResponse:
    """Fetch a stored conversation by id."""
    conversation = await chat_store.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await chat_store.to_response(conversation)


@app.get(
    "/api/chat/conversations/{conversation_id}/ttl",
    response_model=ConversationTtlResponse,
)
async def get_conversation_ttl(conversation_id: str) -> ConversationTtlResponse:
    """Return the remaining TTL for a conversation."""
    ttl_seconds_remaining = await chat_store.get_conversation_ttl(conversation_id)
    return ConversationTtlResponse(
        conversation_id=conversation_id,
        configured_ttl_seconds=settings.chat_session_ttl_seconds,
        ttl_seconds_remaining=ttl_seconds_remaining,
        exists=ttl_seconds_remaining >= 0,
    )


@app.post(
    "/api/chat/conversations/{conversation_id}/messages",
    response_model=ChatReplyResponse,
)
async def create_message(
    conversation_id: str,
    request: ChatStreamRequest,
) -> ChatReplyResponse:
    """Append a user message and generate the assistant reply."""
    async with chat_store.conversation_lock(conversation_id):
        conversation = await chat_store.get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        await chat_store.add_user_message(conversation, request.content)
        try:
            reply = await asyncio.to_thread(
                generate_chat_reply,
                conversation.messages,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        assistant_message = await chat_store.add_assistant_message(
            conversation,
            reply.text,
            structured_data=reply.structured_data,
        )

    return ChatReplyResponse(
        assistant_message=assistant_message,
        conversation=await chat_store.to_response(conversation),
    )
