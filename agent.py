from __future__ import annotations

from datetime import UTC, datetime
from json import dumps
from typing import TYPE_CHECKING, cast

from botocore.exceptions import BotoCoreError, ClientError
from strands import Agent
from strands.models import BedrockModel
from strands.models.mistral import MistralModel
from strands.models.openai import OpenAIModel

from app.config import settings
from app.integrations.listenbrainz.client import (
    logger,
)
from app.integrations.listenbrainz.tools import LISTENBRAINZ_TOOLS
from app.integrations.tautulli.tools import TAUTULLI_TOOLS
from app.schemas import GeneratedChatReply

if TYPE_CHECKING:
    from app.schemas import ChatMessage


HOMESERVER_ASSISTANT_PROMPT = """
You are HomeServer Assistant, a chatbot for a user's personal homeserver apps.

You can help the user by retrieving and explaining information from:
- ListenBrainz for music listening history, music/artist/release information, and stats
- Tautulli for Plex watch history, active streams, and server stats

Your job:
- Answer questions about the user's music, watching, and audiobook activity
- Choose the correct tool based on the request
- Summarize results in plain English
- Never invent stats, timestamps, titles, counts, or progress
- If data is missing or unavailable, say that clearly
- If the request spans multiple services, combine results into a clean recap

Tool routing:
- Use musicbrainz_metadata_lookup to get MusicBrainz metadata and MBIDs for songs, albums, or artists
    - If the user specifies nationality/demonym (e.g., "Korean", "South Korean"), set `country` to the ISO 3166-1 alpha-2 code (e.g., KR)
- Use musicbrainz_release_details to get release details like release date, tracklist, and album credits by MBID
- Use listenbrainz_artist_top_songs to get the top songs for an artist by the artist's MBID

Response style:
- Be friendly and concise
- Do not add any extra sentence before or after that heading.
- Never mention "structured data", "structured section", or UI rendering.
- Do not render placeholders such as {Will be react component with structured data}
- Do NOT output chain-of-thought, reasoning, or thinking tags.
- Do NOT include <thinking> blocks.
- Only output the final answer for the user.
"""


def get_ai_model() -> BedrockModel | OpenAIModel | MistralModel:
    """Return a bedrock model or OpenAI model depending on env MODEL_PROVIDER."""
    if settings.model_provider == "openai":
        return OpenAIModel(
            client_args={
                "api_key": settings.open_ai_key,
            },
            model_id="gpt-4o",
            params={
                "max_tokens": 2000,
                "temperature": 0.2,
            },
        )
    if settings.model_provider == "mistral":
        return MistralModel(
            client_args={
                "api_key": settings.mistral_ai_key,
            },
            model_id="devstral-2512",
        )
    return BedrockModel(model_id=settings.bedrock_model_id)


def create_chat_agent() -> Agent:
    """Create a fresh Strands agent and request-scoped tool result store."""
    model = get_ai_model()

    return Agent(
        model,
        tools=[*LISTENBRAINZ_TOOLS, *TAUTULLI_TOOLS],
    )


def build_chat_prompt(messages: list[ChatMessage]) -> str:
    """Build a plain-text prompt from the stored conversation history."""
    transcript_parts: list[str] = []
    for message in messages:
        entry = f"{message.role.title()}: {message.content}"
        if message.structured_data:
            structured_json = dumps(
                [item.model_dump(mode="json") for item in message.structured_data],
                ensure_ascii=False,
            )
            entry += f"\nStructured data: {structured_json}"
        transcript_parts.append(entry)

    transcript = "\n".join(transcript_parts)
    return (
        f"{HOMESERVER_ASSISTANT_PROMPT}\n\n"
        f"Current date (UTC): {datetime.now(UTC).strftime('%Y-%m-%d')}\n\n"
        "Conversation history:\n"
        f"{transcript}\n\n"
        "Respond as the assistant to the latest user message."
    )


def generate_chat_reply(messages: list[ChatMessage]) -> GeneratedChatReply:
    """Generate a reply from the agent."""
    agent = create_chat_agent()

    try:
        result = agent(
            build_chat_prompt(messages),
            structured_output_model=GeneratedChatReply,
        )
        logger.warning(f"Agent tool results: {result}")
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(str(exc)) from exc

    structured = cast("GeneratedChatReply", result.structured_output)
    if structured is None:
        raise RuntimeError("Agent did not return structured output")

    return structured
