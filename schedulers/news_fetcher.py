"""News fetcher scheduler job."""

import time
from datetime import datetime, timedelta
from typing import Dict, Any

from services.watchlist_service import get_all_tickers
from services.news_service import save_news_items
from news_retriever import fetch_news_data, NewsRetrievalError
from logger import logger
from rate_limit_manager import get_rate_limit_manager


def fetch_all_news_job() -> Dict[str, Any]:
    """Fetch news for all active tickers in the watchlist."""
    job_start = time.perf_counter()
    logger.info("Starting news fetch job...")

    # Check if Alpha Vantage is available
    rate_limiter = get_rate_limit_manager()
    if not rate_limiter.alpha_vantage.is_available():
        remaining = rate_limiter.alpha_vantage.get_remaining_cooldown()
        logger.info(f"Alpha Vantage API in cooldown, {remaining}s remaining. Skipping fetch job.")
        elapsed = time.perf_counter() - job_start
        return {
            "success": False,
            "reason": "alpha_vantage_cooldown",
            "duration": elapsed,
            "total_saved": 0,
            "tickers_processed": 0,
            "error_count": 0
        }

    # Fetch active tickers
    fetch_tickers_start = time.perf_counter()
    tickers = get_all_tickers(include_inactive=False)
    fetch_tickers_elapsed = time.perf_counter() - fetch_tickers_start
    logger.debug(f"Fetched watchlist in {fetch_tickers_elapsed:.3f}s")

    if not tickers:
        logger.info("No active tickers in watchlist, skipping fetch")
        elapsed = time.perf_counter() - job_start
        logger.info(f"News fetch job completed in {elapsed:.3f}s (no active tickers)")
        return {
            "success": True,
            "duration": elapsed,
            "total_saved": 0,
            "tickers_processed": 0,
            "error_count": 0
        }

    logger.info(f"Found {len(tickers)} active tickers to process")

    time_to = datetime.now()
    time_from = time_to - timedelta(hours=6)  # Last 6 hours

    total_saved = 0
    error_count = 0

    for idx, ticker_record in enumerate(tickers, 1):
        ticker = ticker_record.ticker
        try:
            logger.info(f"Processing {idx}/{len(tickers)}: Fetching news for {ticker}...")

            # Fetch news from API
            fetch_start = time.perf_counter()
            news_items = fetch_news_data(
                ticker=ticker,
                time_from=time_from,
                time_to=time_to,
                use_cache=True
            )
            fetch_elapsed = time.perf_counter() - fetch_start
            logger.debug(f"Alpha Vantage API call for {ticker} completed in {fetch_elapsed:.3f}s")

            if news_items:
                # Save to database
                db_start = time.perf_counter()
                saved = save_news_items(ticker, news_items)
                db_elapsed = time.perf_counter() - db_start
                logger.debug(f"Database save for {ticker} completed in {db_elapsed:.3f}s")

                total_saved += saved
                logger.info(f"Saved {saved} new items for {ticker} (found {len(news_items)} total)")
            else:
                logger.info(f"No news found for {ticker}")

        except NewsRetrievalError as e:
            logger.error(f"Failed to fetch news for {ticker}: {e}")
            error_count += 1
        except Exception as e:
            logger.error(f"Unexpected error fetching {ticker}: {e}")
            error_count += 1

    job_elapsed = time.perf_counter() - job_start
    logger.info(
        f"News fetch job completed in {job_elapsed:.3f}s. "
        f"Total saved: {total_saved}, Tickers processed: {len(tickers)}, Errors: {error_count}"
    )

    return {
        "success": True,
        "duration": job_elapsed,
        "total_saved": total_saved,
        "tickers_processed": len(tickers),
        "error_count": error_count
    }


def fetch_news_for_ticker(ticker_symbol: str, hours: int = 24) -> Dict[str, Any]:
    """Fetch news for a specific ticker."""
    job_start = time.perf_counter()
    ticker = ticker_symbol.upper()
    logger.info(f"Starting news fetch for {ticker} (last {hours} hours)...")

    time_to = datetime.now()
    time_from = time_to - timedelta(hours=hours)

    try:
        # Fetch news from API
        fetch_start = time.perf_counter()
        news_items = fetch_news_data(
            ticker=ticker,
            time_from=time_from,
            time_to=time_to,
            use_cache=False  # Fresh data
        )
        fetch_elapsed = time.perf_counter() - fetch_start
        logger.debug(f"Alpha Vantage API call for {ticker} completed in {fetch_elapsed:.3f}s")

        if news_items:
            # Save to database
            db_start = time.perf_counter()
            saved = save_news_items(ticker, news_items)
            db_elapsed = time.perf_counter() - db_start
            logger.debug(f"Database save for {ticker} completed in {db_elapsed:.3f}s")

            job_elapsed = time.perf_counter() - job_start
            logger.info(
                f"Fetched and saved {saved} items for {ticker} in {job_elapsed:.3f}s "
                f"(found {len(news_items)} total)"
            )

            return {
                "success": True,
                "duration": job_elapsed,
                "ticker": ticker,
                "saved": saved,
                "total_found": len(news_items)
            }

        job_elapsed = time.perf_counter() - job_start
        logger.info(f"No news found for {ticker} (completed in {job_elapsed:.3f}s)")
        return {
            "success": True,
            "duration": job_elapsed,
            "ticker": ticker,
            "saved": 0,
            "total_found": 0
        }

    except NewsRetrievalError as e:
        job_elapsed = time.perf_counter() - job_start
        logger.error(f"Failed to fetch news for {ticker}: {e}")
        return {
            "success": False,
            "duration": job_elapsed,
            "ticker": ticker,
            "error": str(e)
        }
