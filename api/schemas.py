"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Enums
# =============================================================================

class NewsStatus(str, Enum):
    """Status of a news item."""
    PENDING = "pending"
    ANALYZED = "analyzed"


class TradingSignal(str, Enum):
    """Trading signal based on sentiment."""
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"


# =============================================================================
# Ticker Schemas
# =============================================================================

class TickerCreate(BaseModel):
    """Schema for creating a new ticker."""
    ticker: str = Field(..., min_length=1, max_length=10, pattern=r"^[A-Z]+$")
    name: Optional[str] = Field(None, max_length=200)


class TickerSentimentResponse(BaseModel):
    """Aggregated sentiment for a ticker."""
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    score: float
    normalized_score: float
    sentiment_label: Optional[str]
    signal: Optional[str]
    confidence: float
    positive_count: int
    negative_count: int
    neutral_count: int
    total_analyzed: int
    total_pending: int
    updated_at: Optional[datetime]


class TickerResponse(BaseModel):
    """Response schema for a ticker."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: Optional[str]
    added_at: datetime
    is_active: bool
    sentiment: Optional[TickerSentimentResponse] = None


class TickerListResponse(BaseModel):
    """Response schema for list of tickers."""
    tickers: List[TickerResponse]
    count: int


# =============================================================================
# News Schemas
# =============================================================================

class NewsItemResponse(BaseModel):
    """Response schema for a news item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    title: str
    summary: str
    published_date: Optional[str]
    source: Optional[str]
    url: Optional[str]
    relevance_score: Optional[float]
    status: NewsStatus
    sentiment: Optional[str] = None
    justification: Optional[str] = None
    fetched_at: datetime
    analyzed_at: Optional[datetime]


class NewsListResponse(BaseModel):
    """Response schema for list of news."""
    news: List[NewsItemResponse]
    count: int
    pending_count: int
    analyzed_count: int


# =============================================================================
# Health Check
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    scheduler: str


# =============================================================================
# Error Response
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    code: Optional[str] = None
