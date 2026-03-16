import httpx

from app.config import settings
from app.integrations.listenbrainz.client import logger
from app.integrations.listenbrainz.models import ErrorResponse

from .models import CurrentActivityResponse


async def fetch_current_tautulli_activity() -> CurrentActivityResponse | ErrorResponse:
    """Fetch Current Tautulli Activity/Streams."""
    url = (
        f"{settings.tautulli_base_url}?apikey={settings.tautulli_key}&cmd=get_activity"
    )
    logger.warning(f"Fetching current Tautulli activity from URL: {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        response.raise_for_status()

    except httpx.TimeoutException:
        return ErrorResponse(error="MusicBrainz request timed out. Please try again.")
    except httpx.HTTPError as exc:
        return ErrorResponse(error=f"MusicBrainz request failed: {exc}")

    if response is None:
        return ErrorResponse(
            error="Tautulli request failed unexpectedly.",
        )

    data = response.json().get("response", {}).get("data", {})

    logger.warning(f"Received response from Tautulli: {response.json()}")

    return CurrentActivityResponse.model_validate(data)
