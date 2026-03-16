from strands import tool

from app.integrations.listenbrainz.models import ErrorResponse
from app.integrations.tautulli.client import fetch_current_tautulli_activity
from app.integrations.tautulli.models import CurrentActivityResponse


@tool
async def tautulli_current_activity() -> CurrentActivityResponse | ErrorResponse:
    """Tool for looking up top songs for an artist from ListenBrainz by artist MBID.

    Must have the MBID for the release:
        - Use musicbrainz_metadata_lookup tool if you need the MBID

    Args:
    request:
        - mbid: MusicBrainz ID of the release to look up (required)

    """
    return await fetch_current_tautulli_activity()
