# Homeserver Agent API

Small FastAPI service that stores chat conversations on disk and generates replies using a Strands agent.

Tools currently included:

- ListenBrainz + MusicBrainz (music history + metadata)
- Tautulli (Plex activity)

## Requirements

- Python 3.14+
- One model provider configured: OpenAI, AWS Bedrock, or Mistral

## Setup

Install dependencies (recommended):

```bash
uv sync
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

Create a `.env` in the repo root (minimum required):

```env
# Required
MODEL_PROVIDER=openai  # openai | bedrock | mistral
LISTENBRAINZ_KEY=...
TAUTULLI_BASE_URL=http://your-tautulli:8181
TAUTULLI_KEY=...

# Provider-specific (pick one)
OPEN_AI_KEY=...        # when MODEL_PROVIDER=openai
MISTRAL_AI_KEY=...     # when MODEL_PROVIDER=mistral

# Bedrock (when MODEL_PROVIDER=bedrock)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.openai.gpt-oss-120b-1:0

# Optional chat storage
CHAT_SESSION_STORAGE_DIR=.strands-sessions
CHAT_SESSION_TTL_SECONDS=2700
CHAT_CONVERSATION_LOCK_TIMEOUT_SECONDS=120
```

## Run

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Docs: http://localhost:8080/docs

## Endpoints

- `GET /health`
- `POST /api/chat/conversations/create`
- `GET /api/chat/conversations/{conversation_id}`
- `GET /api/chat/conversations/{conversation_id}/ttl`
- `POST /api/chat/conversations/{conversation_id}/messages`

## Minimal curl

```bash
curl -s -X POST http://localhost:8080/api/chat/conversations/create
```

```bash
curl -s -X POST \
  http://localhost:8080/api/chat/conversations/<conversation_id>/messages \
  -H 'Content-Type: application/json' \
  -d '{"content":"What are my the top songs by the artist Celine Dion?"}'
```

