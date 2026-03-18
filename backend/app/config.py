from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql://postgres:postgres@db:5432/bracket_tracker"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ESPN API
    espn_api_base_url: str = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
    espn_cache_ttl: int = 300  # 5 minutes

    # OpenClaw WhatsApp
    openclaw_api_url: str | None = None
    openclaw_api_token: str | None = None
    whatsapp_notification_number: str | None = None

    # App settings
    app_name: str = "NCAA Bracket Tracker"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
