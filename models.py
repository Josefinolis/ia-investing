"""Pydantic models for data validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SentimentCategory(str, Enum):
    """Valid sentiment categories."""
    HIGHLY_NEGATIVE = "Highly Negative"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"
    POSITIVE = "Positive"
    HIGHLY_POSITIVE = "Highly Positive"


class NewsItem(BaseModel):
    """Validated news item model."""
    title: str = Field(..., min_length=1, max_length=500)
    summary: str = Field(..., min_length=1)
    published_date: str = Field(..., description="Publication date in API format")
    source: Optional[str] = None
    source_type: Optional[str] = Field(
        None, description="Source type: alpha_vantage, reddit, twitter"
    )
    url: Optional[str] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    engagement_score: Optional[int] = Field(
        None, description="Social engagement (likes, upvotes, etc.)"
    )
    author: Optional[str] = Field(None, description="Author username")
    author_followers: Optional[int] = Field(None, description="Author follower count")

    @field_validator("title", "summary")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    def __str__(self) -> str:
        summary_preview = self.summary[:70] + "..." if len(self.summary) > 70 else self.summary
        return f"Title: {self.title}\nDate: {self.published_date}\nSummary: {summary_preview}"


class SentimentAnalysis(BaseModel):
    """Validated sentiment analysis result."""
    sentiment: SentimentCategory = Field(..., alias="SENTIMENT")
    justification: str = Field(..., alias="JUSTIFICATION", min_length=1)

    class Config:
        populate_by_name = True


class AnalysisResult(BaseModel):
    """Complete analysis result for a news item."""
    news: NewsItem
    analysis: Optional[SentimentAnalysis] = None
    analyzed_at: datetime = Field(default_factory=datetime.now)
    ticker: str
    error: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        return self.analysis is not None and self.error is None


class AnalysisRequest(BaseModel):
    """Request parameters for analysis."""
    ticker: str = Field(..., min_length=1, max_length=10, pattern=r"^[A-Z]+$")
    time_from: datetime
    time_to: datetime

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper()

    @field_validator("time_to")
    @classmethod
    def validate_time_range(cls, v: datetime, info) -> datetime:
        time_from = info.data.get("time_from")
        if time_from and v < time_from:
            raise ValueError("time_to must be after time_from")
        return v


class AnalysisSummary(BaseModel):
    """Summary of analysis results for a ticker."""
    ticker: str
    total_news: int
    analyzed_count: int
    failed_count: int
    sentiment_distribution: dict[str, int]
    average_sentiment_score: Optional[float] = None
    results: List[AnalysisResult]

    @property
    def success_rate(self) -> float:
        if self.total_news == 0:
            return 0.0
        return self.analyzed_count / self.total_news * 100
