"""News retrieval from multiple sources with retry, rate limiting, and caching."""

from datetime import datetime
from typing import List, Optional

from models import NewsItem
from logger import logger, log_error
from news_sources.aggregator import NewsAggregator, get_aggregator
from news_sources.alpha_vantage import AlphaVantageSource, AlphaVantageError


# Re-export for backwards compatibility
NewsRetrievalError = AlphaVantageError


def fetch_news_data(
    ticker: str,
    time_from: datetime,
    time_to: datetime,
    use_cache: bool = True,
    sources: Optional[List[str]] = None,
) -> List[NewsItem]:
    """
    Fetch news data from multiple sources (Alpha Vantage, Reddit, Twitter).

    Args:
        ticker: Stock ticker symbol
        time_from: Start datetime for news search
        time_to: End datetime for news search
        use_cache: Whether to use cached data if available
        sources: Optional list of sources to use (e.g., ["alpha_vantage", "reddit", "twitter"])
                 If None, uses all available sources.

    Returns:
        List of validated NewsItem objects from all sources

    Raises:
        NewsRetrievalError: If unable to fetch news after retries
    """
    aggregator = get_aggregator()

    # If only Alpha Vantage is requested or no other sources available, use direct call
    if sources == ["alpha_vantage"]:
        av_source = AlphaVantageSource()
        return av_source.fetch_news(ticker, time_from, time_to, use_cache=use_cache)

    # Use aggregator for multi-source fetch
    return aggregator.fetch_all(ticker, time_from, time_to, sources_filter=sources)


def fetch_news_alpha_vantage(
    ticker: str,
    time_from: datetime,
    time_to: datetime,
    use_cache: bool = True,
) -> List[NewsItem]:
    """
    Fetch news data from Alpha Vantage only.

    Args:
        ticker: Stock ticker symbol
        time_from: Start datetime for news search
        time_to: End datetime for news search
        use_cache: Whether to use cached data if available

    Returns:
        List of validated NewsItem objects
    """
    source = AlphaVantageSource()
    return source.fetch_news(ticker, time_from, time_to, use_cache=use_cache)


# Backwards compatibility alias
def get_news_data(
    ticker: str,
    time_from: datetime,
    time_to: datetime,
    sources: Optional[List[str]] = None,
) -> List[NewsItem]:
    """
    Alias for fetch_news_data for backwards compatibility.

    Now fetches from multiple sources by default.
    """
    try:
        return fetch_news_data(ticker, time_from, time_to, sources=sources)
    except AlphaVantageError as e:
        log_error(f"Failed to retrieve news: {e}")
        return []
