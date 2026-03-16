from strands import tool

from app.integrations.listenbrainz.client import (
    fetch_listenbrainz_top_recordings_by_artist,
)
from app.integrations.listenbrainz.models import (
    ListenBrainzToolResult,
    ListenBrainzTopRecordingsByArtistRequest,
)


@tool
async def listenbrainz_artist_top_songs(
    request: ListenBrainzTopRecordingsByArtistRequest,
) -> ListenBrainzToolResult:
    """Tool for looking up top songs for an artist from ListenBrainz by artist MBID.

    Must have the MBID for the release:
        - Use musicbrainz_metadata_lookup tool if you need the MBID

    Args:
    request:
        - mbid: MusicBrainz ID of the release to look up (required)

    """
    return await fetch_listenbrainz_top_recordings_by_artist(request)
