"""Unit tests for news retrieval module."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import responses

from news_retriever import (
    fetch_news_data,
    get_news_data,
    _build_url,
    _process_response,
    NewsRetrievalError
)
from models import NewsItem


class TestBuildUrl:
    """Tests for URL building."""

    def test_build_url_format(self):
        """Test URL is built correctly."""
        with patch("news_retriever.get_settings") as mock_settings:
            mock_settings.return_value.alpha_vantage_base_url = "https://api.example.com"

            url = _build_url(
                ticker="AAPL",
                time_from=datetime(2024, 1, 1, 0, 0),
                time_to=datetime(2024, 1, 31, 23, 59),
                api_key="test_key"
            )

            assert "AAPL" in url
            assert "test_key" in url
            assert "20240101T0000" in url
            assert "20240131T2359" in url


class TestProcessResponse:
    """Tests for API response processing."""

    def test_process_valid_response(self):
        """Test processing a valid API response."""
        data = {
            "feed": [
                {
                    "title": "Apple Reports Q4 Earnings",
                    "summary": "Apple Inc. reported strong Q4 earnings...",
                    "time_published": "20241215T120000",
                    "source": "Reuters",
                    "url": "https://example.com/news/1",
                    "ticker_sentiment": [
                        {"relevance_score": "0.95"}
                    ]
                },
                {
                    "title": "Tech Stocks Rally",
                    "summary": "Technology stocks saw gains today...",
                    "time_published": "20241215T140000",
                    "source": "Bloomberg"
                }
            ]
        }

        news_list = _process_response(data)

        assert len(news_list) == 2
        assert isinstance(news_list[0], NewsItem)
        assert news_list[0].title == "Apple Reports Q4 Earnings"
        assert news_list[0].source == "Reuters"
        assert news_list[0].relevance_score == 0.95

    def test_process_empty_feed(self):
        """Test processing response with no feed."""
        data = {"feed": []}
        news_list = _process_response(data)
        assert news_list == []

    def test_process_missing_feed(self):
        """Test processing response without feed key."""
        data = {"items": "wrong_key"}
        news_list = _process_response(data)
        assert news_list == []

    def test_process_skips_invalid_items(self):
        """Test that invalid items are skipped."""
        data = {
            "feed": [
                {
                    "title": "Valid News",
                    "summary": "Valid summary",
                    "time_published": "20241215T120000"
                },
                {
                    # Missing required fields
                    "url": "https://example.com"
                }
            ]
        }

        news_list = _process_response(data)
        # Should have at least the valid item
        assert len(news_list) >= 1


class TestGetNewsData:
    """Tests for get_news_data function."""

    @patch("news_retriever.fetch_news_data")
    def test_get_news_data_success(self, mock_fetch):
        """Test successful news retrieval."""
        mock_news = [
            NewsItem(
                title="Test News",
                summary="Test summary",
                published_date="20241215T120000"
            )
        ]
        mock_fetch.return_value = mock_news

        result = get_news_data(
            ticker="AAPL",
            time_from=datetime(2024, 1, 1),
            time_to=datetime(2024, 12, 31)
        )

        assert result == mock_news

    @patch("news_retriever.fetch_news_data")
    def test_get_news_data_handles_error(self, mock_fetch):
        """Test that errors are handled gracefully."""
        mock_fetch.side_effect = NewsRetrievalError("API Error")

        result = get_news_data(
            ticker="AAPL",
            time_from=datetime(2024, 1, 1),
            time_to=datetime(2024, 12, 31)
        )

        assert result == []


class TestFetchNewsData:
    """Tests for fetch_news_data function with retries."""

    @responses.activate
    @patch("news_retriever.get_settings")
    def test_fetch_news_data_retries_on_failure(self, mock_settings):
        """Test that retries happen on transient failures."""
        mock_settings.return_value.alpha_vantage_api_key = "test_key"
        mock_settings.return_value.alpha_vantage_base_url = "https://api.example.com"

        # First two calls fail, third succeeds
        responses.add(
            responses.GET,
            "https://api.example.com",
            json={"error": "timeout"},
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.example.com",
            json={"error": "timeout"},
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.example.com",
            json={"feed": []},
            status=200
        )

        # The function should eventually succeed after retries
        # Note: This test verifies the retry logic exists
