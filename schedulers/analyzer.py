"""News analyzer scheduler job."""

import time
from typing import Set, Dict, Any

from services.news_service import get_pending_news, update_news_analysis
from services.sentiment_service import update_ticker_sentiment
from ia_analisis import analyze_sentiment, AnalysisError
from logger import logger
from rate_limit_manager import get_rate_limit_manager


def analyze_pending_news_job(batch_size: int = 10) -> Dict[str, Any]:
    """Analyze pending news items."""
    job_start = time.perf_counter()
    logger.info("Starting news analysis job...")

    # Check if Gemini is available
    rate_limiter = get_rate_limit_manager()
    if not rate_limiter.gemini.is_available():
        remaining = rate_limiter.gemini.get_remaining_cooldown()
        logger.info(f"Gemini API in cooldown, {remaining}s remaining. Skipping analysis job.")
        elapsed = time.perf_counter() - job_start
        return {
            "success": False,
            "reason": "gemini_cooldown",
            "duration": elapsed,
            "success_count": 0,
            "error_count": 0
        }

    # Fetch pending news
    fetch_start = time.perf_counter()
    pending_news = get_pending_news(limit=batch_size)
    fetch_elapsed = time.perf_counter() - fetch_start
    logger.debug(f"Fetched pending news in {fetch_elapsed:.3f}s")

    if not pending_news:
        logger.info("No pending news to analyze")
        elapsed = time.perf_counter() - job_start
        logger.info(f"Analysis job completed in {elapsed:.3f}s (no pending news)")
        return {
            "success": True,
            "duration": elapsed,
            "success_count": 0,
            "error_count": 0,
            "tickers_updated": 0
        }

    logger.info(f"Found {len(pending_news)} pending news items to analyze")

    processed_tickers: Set[str] = set()
    success_count = 0
    error_count = 0

    for idx, news in enumerate(pending_news, 1):
        try:
            logger.info(f"Processing {idx}/{len(pending_news)}: {news.title[:50]}...")

            # Call Gemini for sentiment analysis
            analysis_start = time.perf_counter()
            analysis = analyze_sentiment(news.ticker, news.summary)
            analysis_elapsed = time.perf_counter() - analysis_start
            logger.debug(f"Gemini API call completed in {analysis_elapsed:.3f}s")

            if analysis:
                # Update news record with analysis
                db_start = time.perf_counter()
                update_news_analysis(
                    news_id=news.id,
                    sentiment=analysis.sentiment.value,
                    justification=analysis.justification
                )
                db_elapsed = time.perf_counter() - db_start
                logger.debug(f"Database update completed in {db_elapsed:.3f}s")

                processed_tickers.add(news.ticker)
                success_count += 1
                logger.info(f"Successfully analyzed news {news.id} ({news.ticker}): {analysis.sentiment.value}")
            else:
                logger.warning(f"No analysis returned for news {news.id}")
                error_count += 1

        except AnalysisError as e:
            logger.error(f"Analysis error for news {news.id}: {e}")
            error_count += 1
        except Exception as e:
            logger.error(f"Unexpected error analyzing news {news.id}: {e}")
            error_count += 1

    # Update aggregated sentiment for affected tickers
    logger.info(f"Updating sentiment aggregation for {len(processed_tickers)} tickers...")
    sentiment_start = time.perf_counter()
    for ticker in processed_tickers:
        try:
            ticker_start = time.perf_counter()
            update_ticker_sentiment(ticker)
            ticker_elapsed = time.perf_counter() - ticker_start
            logger.debug(f"Updated sentiment for {ticker} in {ticker_elapsed:.3f}s")
        except Exception as e:
            logger.error(f"Failed to update sentiment for {ticker}: {e}")
    sentiment_elapsed = time.perf_counter() - sentiment_start
    logger.debug(f"All sentiment updates completed in {sentiment_elapsed:.3f}s")

    job_elapsed = time.perf_counter() - job_start
    logger.info(
        f"Analysis job completed in {job_elapsed:.3f}s. "
        f"Success: {success_count}, Errors: {error_count}, "
        f"Tickers updated: {len(processed_tickers)}"
    )

    return {
        "success": True,
        "duration": job_elapsed,
        "success_count": success_count,
        "error_count": error_count,
        "tickers_updated": len(processed_tickers)
    }


def analyze_all_pending() -> Dict[str, Any]:
    """Analyze all pending news (no batch limit)."""
    job_start = time.perf_counter()
    logger.info("Analyzing all pending news...")

    # Check if Gemini is available
    rate_limiter = get_rate_limit_manager()
    if not rate_limiter.gemini.is_available():
        remaining = rate_limiter.gemini.get_remaining_cooldown()
        logger.info(f"Gemini API in cooldown, {remaining}s remaining. Skipping analysis.")
        elapsed = time.perf_counter() - job_start
        return {
            "success": False,
            "reason": "gemini_cooldown",
            "duration": elapsed,
            "success_count": 0
        }

    # Fetch pending news
    fetch_start = time.perf_counter()
    pending_news = get_pending_news(limit=1000)  # Large limit
    fetch_elapsed = time.perf_counter() - fetch_start
    logger.debug(f"Fetched pending news in {fetch_elapsed:.3f}s")

    if not pending_news:
        logger.info("No pending news to analyze")
        elapsed = time.perf_counter() - job_start
        return {
            "success": True,
            "duration": elapsed,
            "success_count": 0
        }

    logger.info(f"Found {len(pending_news)} pending news items to analyze")

    processed_tickers: Set[str] = set()
    success_count = 0
    error_count = 0

    for idx, news in enumerate(pending_news, 1):
        try:
            logger.info(f"Processing {idx}/{len(pending_news)}: {news.title[:50]}...")

            analysis_start = time.perf_counter()
            analysis = analyze_sentiment(news.ticker, news.summary)
            analysis_elapsed = time.perf_counter() - analysis_start
            logger.debug(f"Gemini API call completed in {analysis_elapsed:.3f}s")

            if analysis:
                db_start = time.perf_counter()
                update_news_analysis(
                    news_id=news.id,
                    sentiment=analysis.sentiment.value,
                    justification=analysis.justification
                )
                db_elapsed = time.perf_counter() - db_start
                logger.debug(f"Database update completed in {db_elapsed:.3f}s")

                processed_tickers.add(news.ticker)
                success_count += 1
                logger.info(f"Successfully analyzed news {news.id} ({news.ticker}): {analysis.sentiment.value}")
            else:
                error_count += 1

        except Exception as e:
            logger.error(f"Error analyzing news {news.id}: {e}")
            error_count += 1

    # Update all affected tickers
    logger.info(f"Updating sentiment aggregation for {len(processed_tickers)} tickers...")
    sentiment_start = time.perf_counter()
    for ticker in processed_tickers:
        try:
            ticker_start = time.perf_counter()
            update_ticker_sentiment(ticker)
            ticker_elapsed = time.perf_counter() - ticker_start
            logger.debug(f"Updated sentiment for {ticker} in {ticker_elapsed:.3f}s")
        except Exception as e:
            logger.error(f"Failed to update sentiment for {ticker}: {e}")
    sentiment_elapsed = time.perf_counter() - sentiment_start
    logger.debug(f"All sentiment updates completed in {sentiment_elapsed:.3f}s")

    job_elapsed = time.perf_counter() - job_start
    logger.info(f"All pending news analyzed in {job_elapsed:.3f}s. Success: {success_count}, Errors: {error_count}")

    return {
        "success": True,
        "duration": job_elapsed,
        "success_count": success_count,
        "error_count": error_count,
        "tickers_updated": len(processed_tickers)
    }
