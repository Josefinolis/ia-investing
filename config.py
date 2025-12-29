"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    alpha_vantage_api_key: str = Field(..., validation_alias="ALPHA_VANTAGE_API_KEY")
    gemini_api_key: Optional[str] = Field(None, validation_alias="GEMINI_API_KEY")

    # API Configuration
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    gemini_model: str = "gemini-2.5-flash-lite"

    # Rate Limiting
    alpha_vantage_calls_per_minute: int = 5
    gemini_calls_per_minute: int = 15

    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Database
    database_url: str = "sqlite:///ia_trading.db"

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

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
