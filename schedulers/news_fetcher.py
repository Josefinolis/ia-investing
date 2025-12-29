"""News fetcher scheduler job."""

from datetime import datetime, timedelta

from services.watchlist_service import get_all_tickers
from services.news_service import save_news_items
from news_retriever import fetch_news_data, NewsRetrievalError
from logger import logger


def fetch_all_news_job():
    """Fetch news for all active tickers in the watchlist."""
    logger.info("Starting news fetch job...")

    tickers = get_all_tickers(include_inactive=False)

    if not tickers:
        logger.info("No active tickers in watchlist, skipping fetch")
        return

    time_to = datetime.now()
    time_from = time_to - timedelta(hours=6)  # Last 6 hours

    total_saved = 0

    for ticker_record in tickers:
        ticker = ticker_record.ticker
        try:
            logger.info(f"Fetching news for {ticker}...")

            news_items = fetch_news_data(
                ticker=ticker,
                time_from=time_from,
                time_to=time_to,
                use_cache=True
            )

            if news_items:
                saved = save_news_items(ticker, news_items)
                total_saved += saved
                logger.info(f"Saved {saved} new items for {ticker}")
            else:
                logger.info(f"No news found for {ticker}")

        except NewsRetrievalError as e:
            logger.error(f"Failed to fetch news for {ticker}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {ticker}: {e}")

    logger.info(f"News fetch job completed. Total saved: {total_saved}")


def fetch_news_for_ticker(ticker_symbol: str, hours: int = 24):
    """Fetch news for a specific ticker."""
    time_to = datetime.now()
    time_from = time_to - timedelta(hours=hours)

    try:
        news_items = fetch_news_data(
            ticker=ticker_symbol.upper(),
            time_from=time_from,
            time_to=time_to,
            use_cache=False  # Fresh data
        )

        if news_items:
            saved = save_news_items(ticker_symbol.upper(), news_items)
            logger.info(f"Fetched and saved {saved} items for {ticker_symbol}")
            return saved

        return 0

    except NewsRetrievalError as e:
        logger.error(f"Failed to fetch news for {ticker_symbol}: {e}")
        raise
