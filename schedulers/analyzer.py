"""News analyzer scheduler job."""

from typing import Set

from services.news_service import get_pending_news, update_news_analysis
from services.sentiment_service import update_ticker_sentiment
from ia_analisis import analyze_sentiment, AnalysisError
from logger import logger


def analyze_pending_news_job(batch_size: int = 10):
    """Analyze pending news items."""
    logger.info("Starting news analysis job...")

    pending_news = get_pending_news(limit=batch_size)

    if not pending_news:
        logger.info("No pending news to analyze")
        return

    logger.info(f"Found {len(pending_news)} pending news items")

    processed_tickers: Set[str] = set()
    success_count = 0
    error_count = 0

    for news in pending_news:
        try:
            logger.debug(f"Analyzing: {news.title[:50]}...")

            # Call Gemini for sentiment analysis
            analysis = analyze_sentiment(news.ticker, news.summary)

            if analysis:
                # Update news record with analysis
                update_news_analysis(
                    news_id=news.id,
                    sentiment=analysis.sentiment.value,
                    justification=analysis.justification
                )
                processed_tickers.add(news.ticker)
                success_count += 1
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
    for ticker in processed_tickers:
        try:
            update_ticker_sentiment(ticker)
        except Exception as e:
            logger.error(f"Failed to update sentiment for {ticker}: {e}")

    logger.info(
        f"Analysis job completed. "
        f"Success: {success_count}, Errors: {error_count}, "
        f"Tickers updated: {len(processed_tickers)}"
    )


def analyze_all_pending():
    """Analyze all pending news (no batch limit)."""
    logger.info("Analyzing all pending news...")

    pending_news = get_pending_news(limit=1000)  # Large limit

    if not pending_news:
        logger.info("No pending news to analyze")
        return 0

    processed_tickers: Set[str] = set()
    success_count = 0

    for news in pending_news:
        try:
            analysis = analyze_sentiment(news.ticker, news.summary)

            if analysis:
                update_news_analysis(
                    news_id=news.id,
                    sentiment=analysis.sentiment.value,
                    justification=analysis.justification
                )
                processed_tickers.add(news.ticker)
                success_count += 1

        except Exception as e:
            logger.error(f"Error analyzing news {news.id}: {e}")

    # Update all affected tickers
    for ticker in processed_tickers:
        try:
            update_ticker_sentiment(ticker)
        except Exception as e:
            logger.error(f"Failed to update sentiment for {ticker}: {e}")

    return success_count
