from strands import tool

from app.integrations.listenbrainz import (
    MusicBrainzMetadataLookupRequest,
    MusicBrainzMetadataLookupResult,
)
from app.integrations.listenbrainz.client import fetch_musicbrainz_metadata


@tool
async def musicbrainz_metadata_lookup(
    request: MusicBrainzMetadataLookupRequest,
) -> MusicBrainzMetadataLookupResult:
    """Tool for looking up MusicBrainz metadata by name of song/recording or artist name.

    This tool can also be used when metadata/mbid is needed by another tool and the request or previous
     chat messages do not already contain a MusicBrainz ID for the relevant entity.
    For example, if the user asks "What albums have I listened to with my top artist?" and the conversation history does not include the MusicBrainz ID for that artist,
     this tool can be used to look up the ID by artist name.

    Args:
    request:
        - artist: artist name of the listen (optional when looking up by recording name or release)
        - recording: recording name of the listen (optional when looking up by artist or release)
        - release: release name of the listen (optional when looking up by artist or recording)
        - country: Prefer ISO 3166-1 alpha-2 like "KR". If the user provides a country adjective/name (e.g., "korean", "south korea"), pass it and it will be normalized (optional)
        - request_type: one of "artist", "recording", or "release" to indicate the type of entity being looked up (required)

    Example requests:
        1. Search artist by song/recording:
        User: "Which korean artist made the song Talk to You?"
        Tool request:
            {
                "recording": "Talk to You",
                "country": "KR",
                "request_type": "recording"
            }
        2. Search for recording by artist name:
        User: "What albums has the korean artist EXO released?"
        Tool request:
            {
                "artist": "EXO",
                "country": "KR",
                "request_type": "artist"
            }

    """
    return await fetch_musicbrainz_metadata(request)
