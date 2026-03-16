from __future__ import annotations

import logging

import httpx

from app.integrations.listenbrainz import ListenBrainzArtistTopRecordingResponse

from .models import (
    ErrorResponse,
    ListenBrainzToolResult,
    ListenBrainzTopRecordingsByArtistRequest,
    MusicBrainzArtistResponse,
    MusicBrainzMetadataLookupRequest,
    MusicBrainzMetadataLookupResult,
    MusicBrainzRecordingResponse,
    MusicBrainzReleaseDetailsRequest,
    MusicBrainzReleaseDetailsResponse,
    MusicBrainzReleaseResponse,
)

LISTENBRAINZ_BASE_URL = "https://api.listenbrainz.org/1"
MUSICBRAINZ_BASE_URL = "https://musicbrainz.org/ws/2"
HTTP_NO_CONTENT = 204
LISTENBRAINZ_MAX_RETRIES = 2
LISTENBRAINZ_INITIAL_RETRY_DELAY_SECONDS = 0.5
LISTENBRAINZ_TIMEOUT = httpx.Timeout(connect=5.0, read=20.0, write=20.0, pool=5.0)
MUSICBRAINZ_BY_SPLIT_PARTS = 2
MUSICBRAINZ_HEADERS = {
    "User-Agent": "homeserver-agent/1.0 (local development)",
}

logger = logging.getLogger("strands")
logger.setLevel(logging.WARNING)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)


def _build_musicbrainz_query(request: MusicBrainzMetadataLookupRequest) -> str:
    query_parts: list[str] = []
    for field_name in ("artist", "recording", "release", "country"):
        value = getattr(request, field_name)
        if not value:
            continue

        escaped_value = " ".join(value.strip().strip('"').strip("'").split()).replace(
            '"',
            r"\"",
        )
        query_parts.append(f'{field_name}:"{escaped_value}"')

    return " AND ".join(query_parts)


async def _request_musicbrainz(
    url: str,
) -> tuple[httpx.Response | None, str | None]:
    try:
        async with httpx.AsyncClient(
            timeout=LISTENBRAINZ_TIMEOUT,
            headers=MUSICBRAINZ_HEADERS,
        ) as client:
            response = await client.get(url)

        response.raise_for_status()
    except httpx.TimeoutException:
        return None, "MusicBrainz request timed out. Please try again."
    except httpx.HTTPError as exc:
        return None, f"MusicBrainz request failed: {exc}"

    return response, None


async def fetch_musicbrainz_metadata(
    request: MusicBrainzMetadataLookupRequest,
) -> MusicBrainzMetadataLookupResult:
    """Fetch metadata for a recording, artist, or release from MusicBrainz ."""
    if isinstance(request, dict):
        request = MusicBrainzMetadataLookupRequest.model_validate(request)

    query = _build_musicbrainz_query(request)
    if not query:
        return ErrorResponse(error="No valid query parameters provided.")

    url = str(
        httpx.URL(
            f"{MUSICBRAINZ_BASE_URL}/{request.request_type}/",
        ).copy_merge_params(
            httpx.QueryParams(
                {
                    "query": query,
                    "fmt": "json",
                    "limit": 10,
                },
            ),
        ),
    )

    response, error = await _request_musicbrainz(url)

    logger.warning(query)

    if error:
        return ErrorResponse(
            error=error,
        )
    if response is None:
        return ErrorResponse(
            error="MusicBrainz request failed unexpectedly.",
        )

    if response.status_code == HTTP_NO_CONTENT or not response.text.strip():
        return ErrorResponse(
            error="No metadata found for the provided request.",
        )

    if request.request_type == "recording":
        return MusicBrainzRecordingResponse.model_validate(response.json())
    if request.request_type == "artist":
        return MusicBrainzArtistResponse.model_validate(response.json())
    if request.request_type == "release":
        return MusicBrainzReleaseResponse.model_validate(response.json())
    return ErrorResponse(
        error=f"Unsupported request type: {request.request_type}",
    )


async def fetch_musicbrainz_release_details(
    request: MusicBrainzReleaseDetailsRequest,
) -> MusicBrainzMetadataLookupResult:
    """Fetch release details for a MusicBrainz release by MBID. Gets tracks on the release/album."""
    if isinstance(request, dict):
        request = MusicBrainzReleaseDetailsRequest.model_validate(request)

    url = str(
        httpx.URL(
            f"{MUSICBRAINZ_BASE_URL}/release/{request.mbid}",
        ).copy_merge_params(
            httpx.QueryParams(
                {
                    "fmt": "json",
                    "limit": 10,
                    "inc": "recordings",
                },
            ),
        ),
    )

    response, error = await _request_musicbrainz(url)

    if error:
        return ErrorResponse(
            error=error,
        )
    if response is None:
        return ErrorResponse(
            error="MusicBrainz request failed unexpectedly.",
        )

    if response.status_code == HTTP_NO_CONTENT or not response.text.strip():
        return ErrorResponse(
            error="No metadata found for the provided request.",
        )

    return MusicBrainzReleaseDetailsResponse.model_validate(response.json())


async def fetch_listenbrainz_top_recordings_by_artist(
    request: ListenBrainzTopRecordingsByArtistRequest,
) -> ListenBrainzToolResult:
    """Fetch top recordings for an artist from ListenBrainz. Requires artist mbid."""
    if isinstance(request, dict):
        request = ListenBrainzTopRecordingsByArtistRequest.model_validate(request)

    logger.warning(request)
    url = f"{LISTENBRAINZ_BASE_URL}/popularity/top-recordings-for-artist/{request.artist_mbid}"

    logger.warning(url)
    response, error = await _request_musicbrainz(url)

    if error:
        return ErrorResponse(
            error=error,
        )
    if response is None:
        return ErrorResponse(
            error="ListenBrainz request failed unexpectedly.",
        )

    if response.status_code == HTTP_NO_CONTENT or not response.text.strip():
        return ErrorResponse(
            error="No metadata found for the provided artist.",
        )
    logger.warning(response.json())

    return ListenBrainzArtistTopRecordingResponse.model_validate(response.json())
