from app.integrations.listenbrainz.tools.listenbrainz_artist_top_songs import (
    listenbrainz_artist_top_songs,
)
from app.integrations.listenbrainz.tools.musicbrainz_release_details import (
    musicbrainz_release_details,
)
from app.integrations.listenbrainz.tools.musizbrains_metadata_lookup import (
    musicbrainz_metadata_lookup,
)

LISTENBRAINZ_TOOLS = [
    musicbrainz_metadata_lookup,
    musicbrainz_release_details,
    listenbrainz_artist_top_songs,
]
