from pydantic import BaseModel, ConfigDict, Field


class CurrentActivitySession(BaseModel):
    """A single session from the Tautulli current activity endpoint."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    added_at: str
    aspect_ratio: str
    audio_codec: str
    bandwidth: str | int
    audio_decision: str
    full_title: str
    quality_profile: str
    video_resolution: str
    product: str
    ip_address: str
    platform: str
    user: str
    user_id: int
    username: str
    video_decision: str
    transcode_decision: str
    stream_video_codec: str
    stream_audio_language: str
    stream_video_full_resolution: str
    thumb: str


class CurrentActivityResponse(BaseModel):
    """Structured result for a Tautulli current activity request."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    total_bandwidth: int
    sessions: list[CurrentActivitySession] = Field(default_factory=list)
    stream_count: str | int
    stream_count_transcode: int
    stream_count_direct_play: int
    stream_count_direct_stream: int
