"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    alpha_vantage_api_key: str = Field(..., validation_alias="ALPHA_VANTAGE_API_KEY")
    gemini_api_key: Optional[str] = Field(None, validation_alias="GEMINI_API_KEY")

    # API Configuration
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    gemini_model: str = "gemini-2.5-flash-lite"

    # Reddit API Configuration
    reddit_client_id: Optional[str] = Field(None, validation_alias="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(
        None, validation_alias="REDDIT_CLIENT_SECRET"
    )
    reddit_user_agent: str = "ia_trading/1.0"
    reddit_subreddits: str = Field(
        "wallstreetbets,stocks,investing,stockmarket,options",
        validation_alias="REDDIT_SUBREDDITS",
    )
    reddit_min_score: int = Field(10, validation_alias="REDDIT_MIN_SCORE")

    # Twitter/X Configuration (snscrape)
    twitter_enabled: bool = Field(True, validation_alias="TWITTER_ENABLED")
    twitter_min_likes: int = Field(10, validation_alias="TWITTER_MIN_LIKES")
    twitter_min_retweets: int = Field(5, validation_alias="TWITTER_MIN_RETWEETS")
    twitter_max_results: int = Field(50, validation_alias="TWITTER_MAX_RESULTS")

    # Rate Limiting
    alpha_vantage_calls_per_minute: int = 5
    gemini_calls_per_minute: int = 15

    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Database
    database_url: Optional[str] = Field(None, validation_alias="DATABASE_URL")
    database_fallback_url: str = "sqlite:///ia_trading.db"

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Scheduler
    scheduler_enabled: bool = Field(False, validation_alias="SCHEDULER_ENABLED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
