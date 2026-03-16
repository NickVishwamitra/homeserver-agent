from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class MusicBrainzBaseModel(BaseModel):
    """Base model for MusicBrainz response fragments."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class MusicBrainzMetadataLookupRequest(BaseModel):
    """Request model for looking up MusicBrainz metadata by artist, recording, or release."""

    artist: str | None = None
    recording: str | None = None
    release: str | None = None
    country: str | None = None
    request_type: Literal["artist", "recording", "release"] = Field(default="recording")


class MusicBrainzArtist(MusicBrainzBaseModel):
    """Minimal artist reference used in multiple MusicBrainz responses."""

    id: str
    name: str


class MusicBrainzArtistCredit(MusicBrainzBaseModel):
    """Artist credit entry used by recording and release responses."""

    artist: MusicBrainzArtist


class MusicBrainzArea(MusicBrainzBaseModel):
    """Subset of area information for an artist."""

    id: str
    name: str


class MusicBrainzAlias(MusicBrainzBaseModel):
    """Subset of an artist alias."""

    name: str


class MusicBrainzReleaseGroup(MusicBrainzBaseModel):
    """Subset of release-group information for a release."""

    id: str
    title: str


class MusicBrainzRecordingRelease(MusicBrainzBaseModel):
    """Subset of release information attached to a recording result."""

    id: str
    title: str
    country: str | None = None
    date: str | None = None


class MusicBrainzRecordingResponse(MusicBrainzBaseModel):
    """Subset of a MusicBrainz recording search response."""

    recordings: list[MusicBrainzRecordingResponse.Recording]

    class Recording(MusicBrainzBaseModel):
        """Subset of a MusicBrainz recording result."""

        id: str
        title: str
        first_release_date: str | None = Field(default=None, alias="first-release-date")
        artist_credit: list[MusicBrainzArtistCredit] | None = Field(
            default=None,
            alias="artist-credit",
        )
        releases: list[MusicBrainzRecordingRelease] | None = None


class MusicBrainzArtistResponse(MusicBrainzBaseModel):
    """Subset of a MusicBrainz artist search response."""

    artists: list[MusicBrainzArtistResponse.Artist]

    class Artist(MusicBrainzBaseModel):
        """Subset of a MusicBrainz artist result."""

        id: str
        type: str | None = None
        name: str
        country: str | None = None
        area: MusicBrainzArea | None = None
        aliases: list[MusicBrainzAlias] | None = None


class MusicBrainzReleaseDetailsRequest(BaseModel):
    """Request model for looking up MusicBrainz release details by MBID."""

    mbid: str
    limit: int | None = None


class MusicBrainzReleaseResponse(MusicBrainzBaseModel):
    """Subset of a MusicBrainz release search response."""

    releases: list[MusicBrainzReleaseResponse.Release]

    class Release(MusicBrainzBaseModel):
        """Subset of a MusicBrainz release result."""

        id: str
        title: str
        artist_credit: list[MusicBrainzArtistCredit] | None = Field(
            default=None,
            alias="artist-credit",
        )
        release_group: MusicBrainzReleaseGroup | None = Field(
            default=None,
            alias="release-group",
        )
        date: str | None = None
        track_count: int | None = Field(default=None, alias="track-count")


class MusicBrainzReleaseDetailsResponse(BaseModel):
    """Subset of a MusicBrainz release lookup response with track listings."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    title: str
    date: str | None = None
    track_count: int | None = Field(default=None, alias="track-count")
    media: list[MusicBrainzReleaseDetailsResponse.Media] | None = None

    class Recording(BaseModel):
        """Subset of a track's linked recording."""

        model_config = ConfigDict(populate_by_name=True, extra="ignore")

        id: str
        title: str

    class Track(BaseModel):
        """Subset of a release track."""

        model_config = ConfigDict(populate_by_name=True, extra="ignore")

        id: str
        number: str | None = None
        title: str
        length: int | None = None
        recording: MusicBrainzReleaseDetailsResponse.Recording | None = None

    class Media(BaseModel):
        """Subset of a release medium."""

        model_config = ConfigDict(populate_by_name=True, extra="ignore")

        id: str
        format: str | None = None
        track_count: int | None = Field(default=None, alias="track-count")
        tracks: list[MusicBrainzReleaseDetailsResponse.Track] | None = None


class ErrorResponse(MusicBrainzBaseModel):
    """Error result for MusicBrainz lookup."""

    error: str


class ListenBrainzTopRecordingsByArtistRequest(BaseModel):
    """Request model for looking up ListenBrainz top recordings for an artist by MBID."""

    artist_mbid: str


class ListenBrainzArtistTopRecordingItem(BaseModel):
    """Minimal subset of a ListenBrainz top recordings item."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    artist_mbids: list[str]
    artist_name: str
    recording_mbid: str
    recording_name: str
    release_mbid: str | None = None
    release_name: str | None = None
    total_listen_count: int | None = None
    total_user_count: int | None = None


class ListenBrainzArtistTopRecordingResponse(
    RootModel[list[ListenBrainzArtistTopRecordingItem]],
):
    """List response for top recordings."""


MusicBrainzMetadataLookupResult = (
    MusicBrainzRecordingResponse
    | MusicBrainzArtistResponse
    | MusicBrainzReleaseResponse
    | ErrorResponse
    | MusicBrainzReleaseDetailsResponse
)

ListenBrainzToolResult = ListenBrainzArtistTopRecordingResponse | ErrorResponse
