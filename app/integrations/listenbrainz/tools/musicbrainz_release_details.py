from strands import tool

from app.integrations.listenbrainz import MusicBrainzMetadataLookupResult
from app.integrations.listenbrainz.client import fetch_musicbrainz_release_details
from app.integrations.listenbrainz.models import MusicBrainzReleaseDetailsRequest


@tool
async def musicbrainz_release_details(
    request: MusicBrainzReleaseDetailsRequest,
) -> MusicBrainzMetadataLookupResult:
    """Tool for looking up MusicBrainz release details by MBID. Gets tracks on the release/album.

    Must have the MBID for the release:
        - Use musicbrainz_metadata_lookup tool if you need the MBID

    Args:
    request:
        - mbid: MusicBrainz ID of the release to look up (required)
        - limit: maximum number of tracks to return. If not specified, all tracks will be returned,
         for user request that includes number of tracks to show (optional)

    """
    return await fetch_musicbrainz_release_details(request)
