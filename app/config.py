from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_provider: str
    listenbrainz_key: str
    chat_session_ttl_seconds: int = 2700
    chat_session_storage_dir: str = ".strands-sessions"
    chat_conversation_lock_timeout_seconds: int = 120
    open_ai_key: str | None = None
    mistral_ai_key: str | None = None
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "us.openai.gpt-oss-120b-1:0"
    tautulli_base_url: str
    tautulli_key: str
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()  # ty:ignore[missing-argument]
