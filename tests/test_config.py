"""Unit tests for configuration management."""

import os
import pytest
from unittest.mock import patch

from config import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_with_env_vars(self):
        """Test settings load from environment variables."""
        with patch.dict(os.environ, {
            "ALPHA_VANTAGE_API_KEY": "test_av_key",
            "GEMINI_API_KEY": "test_gemini_key"
        }):
            settings = Settings()
            assert settings.alpha_vantage_api_key == "test_av_key"
            assert settings.gemini_api_key == "test_gemini_key"

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {
            "ALPHA_VANTAGE_API_KEY": "test_key"
        }):
            settings = Settings()
            assert settings.alpha_vantage_base_url == "https://www.alphavantage.co/query"
            assert settings.gemini_model == "gemini-2.5-flash"
            assert settings.max_retries == 3
            assert settings.log_level == "INFO"

    def test_missing_required_key_fails(self):
        """Test that missing required API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                Settings()

    def test_rate_limit_defaults(self):
        """Test rate limiting default values."""
        with patch.dict(os.environ, {
            "ALPHA_VANTAGE_API_KEY": "test_key"
        }):
            settings = Settings()
            assert settings.alpha_vantage_calls_per_minute == 5
            assert settings.gemini_calls_per_minute == 15


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_singleton(self):
        """Test that get_settings returns the same instance."""
        with patch.dict(os.environ, {
            "ALPHA_VANTAGE_API_KEY": "test_key"
        }):
            # Reset the global settings
            import config
            config._settings = None

            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2
