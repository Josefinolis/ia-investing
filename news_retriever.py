"""News retrieval from Alpha Vantage API with retry, rate limiting, and caching."""

import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import get_settings
from models import NewsItem
from logger import logger, log_api_call, log_error, log_warning
from cache import news_cache
from rate_limit_manager import get_rate_limit_manager

DATE_FORMAT = "%Y%m%dT%H%M"


class NewsRetrievalError(Exception):
    """Custom exception for news retrieval errors."""
    pass


@sleep_and_retry
@limits(calls=5, period=60)
def _rate_limited_request(url: str) -> requests.Response:
    """Make a rate-limited HTTP request."""
    return requests.get(url, timeout=30)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.RequestException, NewsRetrievalError)),
    before_sleep=lambda retry_state: logger.debug(
        f"Retry attempt {retry_state.attempt_number} after error"
    )
)
def fetch_news_data(
    ticker: str,
    time_from: datetime,
    time_to: datetime,
    use_cache: bool = True
) -> List[NewsItem]:
    """
    Fetch news data from Alpha Vantage API with retry, rate limiting, and caching.

    Args:
        ticker: Stock ticker symbol
        time_from: Start datetime for news search
        time_to: End datetime for news search
        use_cache: Whether to use cached data if available

    Returns:
        List of validated NewsItem objects

    Raises:
        NewsRetrievalError: If unable to fetch news after retries
    """
    # Check if Alpha Vantage is in cooldown
    rate_limiter = get_rate_limit_manager()
    if not rate_limiter.alpha_vantage.is_available():
        remaining = rate_limiter.alpha_vantage.get_remaining_cooldown()
        logger.warning(
            f"Alpha Vantage API in cooldown, {remaining}s remaining. Skipping fetch."
        )
        raise NewsRetrievalError(f"API in cooldown, {remaining}s remaining")

    settings = get_settings()

    # Check cache first
    cache_key_from = time_from.strftime(DATE_FORMAT)
    cache_key_to = time_to.strftime(DATE_FORMAT)

    if use_cache:
        cached_data = news_cache.get(ticker, cache_key_from, cache_key_to)
        if cached_data:
            logger.info(f"Using cached news data for {ticker}")
            return [NewsItem(**item) for item in cached_data]

    url = _build_url(ticker, time_from, time_to, settings.alpha_vantage_api_key)

    try:
        log_api_call("Alpha Vantage", f"NEWS_SENTIMENT for {ticker}")
        response = _rate_limited_request(url)
        response.raise_for_status()
        data = response.json()

        # Check for API error messages
        if "Error Message" in data:
            error_msg = data['Error Message']
            raise NewsRetrievalError(f"API Error: {error_msg}")

        # Check for rate limit messages
        if "Note" in data:
            note = data['Note']
            log_warning(f"API Note: {note}")

            # Check if it's a rate limit message
            if "rate limit" in note.lower() or "frequency" in note.lower() or "call volume" in note.lower():
                rate_limiter.alpha_vantage.enter_cooldown(
                    f"Rate limit exceeded: {note}",
                    cooldown_seconds=60
                )
                raise NewsRetrievalError(f"Rate limit exceeded: {note}")

        # Check for Information messages (also used for rate limiting)
        if "Information" in data:
            info = data['Information']
            if "rate limit" in info.lower() or "frequency" in info.lower():
                rate_limiter.alpha_vantage.enter_cooldown(
                    f"Rate limit exceeded: {info}",
                    cooldown_seconds=60
                )
                raise NewsRetrievalError(f"Rate limit exceeded: {info}")

        news_list = _process_response(data)

        # Cache the results
        if use_cache and news_list:
            cache_data = [item.model_dump() for item in news_list]
            news_cache.set(cache_data, ticker, cache_key_from, cache_key_to)

        return news_list

    except requests.exceptions.Timeout:
        log_error("Request timed out")
        raise NewsRetrievalError("Request timed out")

    except requests.exceptions.HTTPError as e:
        # Check for 429 status code
        if e.response.status_code == 429:
            rate_limiter.alpha_vantage.enter_cooldown(
                "Rate limit exceeded (429)",
                cooldown_seconds=60
            )
            logger.error(f"Alpha Vantage rate limit exceeded: {e}")
            raise NewsRetrievalError("Rate limit exceeded (429)")

        log_error("HTTP request failed", e)
        raise NewsRetrievalError(f"HTTP request failed: {e}")

    except requests.exceptions.RequestException as e:
        log_error("HTTP request failed", e)
        raise NewsRetrievalError(f"HTTP request failed: {e}")

    except ValueError as e:
        log_error("Invalid JSON response", e)
        raise NewsRetrievalError("API returned invalid JSON")


def _build_url(
    ticker: str,
    time_from: datetime,
    time_to: datetime,
    api_key: str
) -> str:
    """Build the Alpha Vantage API URL."""
    settings = get_settings()

    time_from_param = time_from.strftime(DATE_FORMAT)
    time_to_param = time_to.strftime(DATE_FORMAT)

    return (
        f"{settings.alpha_vantage_base_url}?function=NEWS_SENTIMENT"
        f"&tickers={ticker}&apikey={api_key}"
        f"&time_from={time_from_param}&time_to={time_to_param}"
    )


def _process_response(data: Dict[str, Any]) -> List[NewsItem]:
    """Process API response and convert to NewsItem models."""
    raw_feed: Optional[List[dict]] = data.get("feed")

    if not raw_feed:
        logger.debug("No news items in API response")
        return []

    news_list: List[NewsItem] = []

    for item in raw_feed:
        try:
            # Extract ticker-specific relevance if available
            relevance_score = None
            ticker_sentiment = item.get("ticker_sentiment", [])
            if ticker_sentiment:
                relevance_score = float(ticker_sentiment[0].get("relevance_score", 0))

            news_item = NewsItem(
                title=item.get("title", "Title Not Available"),
                summary=item.get("summary", "Summary Not Available"),
                published_date=item.get("time_published", "Date Not Available"),
                source=item.get("source"),
                url=item.get("url"),
                relevance_score=relevance_score
            )
            news_list.append(news_item)

        except Exception as e:
            logger.warning(f"Skipping invalid news item: {e}")
            continue

    logger.info(f"Retrieved {len(news_list)} news items")
    return news_list


# Backwards compatibility alias
def get_news_data(ticker: str, time_from: datetime, time_to: datetime) -> List[NewsItem]:
    """Alias for fetch_news_data for backwards compatibility."""
    try:
        return fetch_news_data(ticker, time_from, time_to)
    except NewsRetrievalError as e:
        log_error(f"Failed to retrieve news: {e}")
        return []
