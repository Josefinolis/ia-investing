"""Unit tests for data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models import (
    NewsItem,
    SentimentCategory,
    SentimentAnalysis,
    AnalysisResult,
    AnalysisRequest,
    AnalysisSummary
)


class TestNewsItem:
    """Tests for NewsItem model."""

    def test_valid_news_item(self):
        """Test creating a valid news item."""
        news = NewsItem(
            title="Apple announces new product",
            summary="Apple Inc. has announced a new innovative product...",
            published_date="20241215T120000"
        )
        assert news.title == "Apple announces new product"
        assert news.summary == "Apple Inc. has announced a new innovative product..."

    def test_news_item_with_optional_fields(self):
        """Test news item with all optional fields."""
        news = NewsItem(
            title="Test News",
            summary="Test summary",
            published_date="20241215T120000",
            source="Reuters",
            url="https://example.com/news",
            relevance_score=0.85
        )
        assert news.source == "Reuters"
        assert news.url == "https://example.com/news"
        assert news.relevance_score == 0.85

    def test_news_item_strips_whitespace(self):
        """Test that title and summary are stripped."""
        news = NewsItem(
            title="  Padded Title  ",
            summary="  Padded Summary  ",
            published_date="20241215T120000"
        )
        assert news.title == "Padded Title"
        assert news.summary == "Padded Summary"

    def test_news_item_empty_title_fails(self):
        """Test that empty title fails validation."""
        with pytest.raises(ValidationError):
            NewsItem(
                title="",
                summary="Valid summary",
                published_date="20241215T120000"
            )

    def test_news_item_relevance_score_range(self):
        """Test relevance score validation."""
        # Valid scores
        news = NewsItem(
            title="Test",
            summary="Test",
            published_date="20241215T120000",
            relevance_score=0.5
        )
        assert news.relevance_score == 0.5

        # Invalid score (> 1.0)
        with pytest.raises(ValidationError):
            NewsItem(
                title="Test",
                summary="Test",
                published_date="20241215T120000",
                relevance_score=1.5
            )

    def test_news_item_str_representation(self):
        """Test string representation."""
        news = NewsItem(
            title="Test Title",
            summary="A" * 100,  # Long summary
            published_date="20241215T120000"
        )
        str_repr = str(news)
        assert "Test Title" in str_repr
        assert "..." in str_repr  # Should be truncated


class TestSentimentCategory:
    """Tests for SentimentCategory enum."""

    def test_all_categories_exist(self):
        """Test all expected categories exist."""
        categories = [
            SentimentCategory.HIGHLY_NEGATIVE,
            SentimentCategory.NEGATIVE,
            SentimentCategory.NEUTRAL,
            SentimentCategory.POSITIVE,
            SentimentCategory.HIGHLY_POSITIVE
        ]
        assert len(categories) == 5

    def test_category_values(self):
        """Test category string values."""
        assert SentimentCategory.HIGHLY_POSITIVE.value == "Highly Positive"
        assert SentimentCategory.NEUTRAL.value == "Neutral"


class TestSentimentAnalysis:
    """Tests for SentimentAnalysis model."""

    def test_valid_sentiment_analysis(self):
        """Test creating valid sentiment analysis."""
        analysis = SentimentAnalysis(
            SENTIMENT="Positive",
            JUSTIFICATION="The news indicates growth potential."
        )
        assert analysis.sentiment == SentimentCategory.POSITIVE
        assert analysis.justification == "The news indicates growth potential."

    def test_sentiment_analysis_with_alias(self):
        """Test that field aliases work."""
        # Using aliases (API format)
        analysis = SentimentAnalysis(
            SENTIMENT="Negative",
            JUSTIFICATION="Revenue decline reported."
        )
        assert analysis.sentiment == SentimentCategory.NEGATIVE

    def test_invalid_sentiment_fails(self):
        """Test that invalid sentiment value fails."""
        with pytest.raises(ValidationError):
            SentimentAnalysis(
                SENTIMENT="Very Good",  # Invalid
                JUSTIFICATION="Test"
            )


class TestAnalysisRequest:
    """Tests for AnalysisRequest model."""

    def test_valid_request(self):
        """Test creating a valid analysis request."""
        request = AnalysisRequest(
            ticker="AAPL",
            time_from=datetime(2024, 1, 1),
            time_to=datetime(2024, 12, 31)
        )
        assert request.ticker == "AAPL"

    def test_ticker_uppercase_conversion(self):
        """Test that ticker is converted to uppercase."""
        request = AnalysisRequest(
            ticker="aapl",
            time_from=datetime(2024, 1, 1),
            time_to=datetime(2024, 12, 31)
        )
        assert request.ticker == "AAPL"

    def test_invalid_ticker_format_fails(self):
        """Test that invalid ticker format fails."""
        with pytest.raises(ValidationError):
            AnalysisRequest(
                ticker="123",  # Numbers not allowed
                time_from=datetime(2024, 1, 1),
                time_to=datetime(2024, 12, 31)
            )

    def test_time_range_validation(self):
        """Test that time_to must be after time_from."""
        with pytest.raises(ValidationError):
            AnalysisRequest(
                ticker="AAPL",
                time_from=datetime(2024, 12, 31),
                time_to=datetime(2024, 1, 1)  # Before time_from
            )


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_successful_result(self):
        """Test a successful analysis result."""
        news = NewsItem(
            title="Test",
            summary="Test summary",
            published_date="20241215T120000"
        )
        analysis = SentimentAnalysis(
            SENTIMENT="Positive",
            JUSTIFICATION="Good news"
        )
        result = AnalysisResult(
            news=news,
            analysis=analysis,
            ticker="AAPL"
        )
        assert result.is_successful is True
        assert result.error is None

    def test_failed_result(self):
        """Test a failed analysis result."""
        news = NewsItem(
            title="Test",
            summary="Test summary",
            published_date="20241215T120000"
        )
        result = AnalysisResult(
            news=news,
            analysis=None,
            ticker="AAPL",
            error="API timeout"
        )
        assert result.is_successful is False
        assert result.error == "API timeout"


class TestAnalysisSummary:
    """Tests for AnalysisSummary model."""

    def test_summary_success_rate(self):
        """Test success rate calculation."""
        summary = AnalysisSummary(
            ticker="AAPL",
            total_news=10,
            analyzed_count=8,
            failed_count=2,
            sentiment_distribution={
                "Highly Positive": 2,
                "Positive": 3,
                "Neutral": 2,
                "Negative": 1,
                "Highly Negative": 0
            },
            results=[]
        )
        assert summary.success_rate == 80.0

    def test_summary_zero_news(self):
        """Test success rate with zero news."""
        summary = AnalysisSummary(
            ticker="AAPL",
            total_news=0,
            analyzed_count=0,
            failed_count=0,
            sentiment_distribution={},
            results=[]
        )
        assert summary.success_rate == 0.0
