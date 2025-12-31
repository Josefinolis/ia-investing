"""Watchlist management service."""

import time
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database import WatchlistTicker, TickerSentiment, get_database
from logger import logger


def get_all_tickers(include_inactive: bool = False) -> List[WatchlistTicker]:
    """Get all tickers from watchlist."""
    start = time.perf_counter()
    logger.info("[WATCHLIST] get_all_tickers: Getting database connection...")

    db = get_database()
    logger.info("[WATCHLIST] get_all_tickers: Opening session...")

    with db.get_session() as session:
        query_start = time.perf_counter()
        query = session.query(WatchlistTicker)
        if not include_inactive:
            query = query.filter(WatchlistTicker.is_active == True)
        tickers = query.order_by(WatchlistTicker.added_at.desc()).all()
        query_elapsed = time.perf_counter() - query_start
        logger.info(f"[WATCHLIST] get_all_tickers: Query executed in {query_elapsed:.3f}s, found {len(tickers)} tickers")

        # Eagerly load relationships before session closes
        for ticker in tickers:
            _ = ticker.sentiment  # Force load
        session.expunge_all()

        elapsed = time.perf_counter() - start
        logger.info(f"[WATCHLIST] get_all_tickers: Completed in {elapsed:.3f}s")
        return tickers


def get_ticker(ticker_symbol: str) -> Optional[WatchlistTicker]:
    """Get a specific ticker by symbol."""
    db = get_database()
    with db.get_session() as session:
        ticker = session.query(WatchlistTicker).filter(
            WatchlistTicker.ticker == ticker_symbol.upper()
        ).first()
        if ticker:
            _ = ticker.sentiment  # Force load
            session.expunge(ticker)
        return ticker


def add_ticker(ticker_symbol: str, name: Optional[str] = None) -> WatchlistTicker:
    """Add a ticker to the watchlist."""
    start = time.perf_counter()
    logger.info(f"[WATCHLIST] add_ticker: Starting for {ticker_symbol.upper()}")

    db = get_database()
    logger.info("[WATCHLIST] add_ticker: Opening session...")

    with db.get_session() as session:
        # Check if ticker already exists
        logger.info("[WATCHLIST] add_ticker: Checking if ticker exists...")
        check_start = time.perf_counter()
        existing = session.query(WatchlistTicker).filter(
            WatchlistTicker.ticker == ticker_symbol.upper()
        ).first()
        check_elapsed = time.perf_counter() - check_start
        logger.info(f"[WATCHLIST] add_ticker: Existence check completed in {check_elapsed:.3f}s")

        if existing:
            # Reactivate if inactive
            if not existing.is_active:
                existing.is_active = True
                if name:
                    existing.name = name
                commit_start = time.perf_counter()
                session.commit()
                commit_elapsed = time.perf_counter() - commit_start
                logger.info(f"[WATCHLIST] add_ticker: Reactivated ticker {ticker_symbol.upper()} (commit: {commit_elapsed:.3f}s)")
            _ = existing.sentiment  # Force load relationship
            session.expunge_all()
            elapsed = time.perf_counter() - start
            logger.info(f"[WATCHLIST] add_ticker: Returned existing ticker in {elapsed:.3f}s")
            return existing

        # Create new ticker
        logger.info("[WATCHLIST] add_ticker: Creating new ticker...")
        ticker = WatchlistTicker(
            ticker=ticker_symbol.upper(),
            name=name,
            added_at=datetime.now(),
            is_active=True
        )
        session.add(ticker)
        commit1_start = time.perf_counter()
        session.commit()
        commit1_elapsed = time.perf_counter() - commit1_start
        logger.info(f"[WATCHLIST] add_ticker: First commit (ticker) in {commit1_elapsed:.3f}s")

        # Create empty sentiment record
        logger.info("[WATCHLIST] add_ticker: Creating sentiment record...")
        sentiment = TickerSentiment(
            ticker=ticker_symbol.upper(),
            score=0.0,
            normalized_score=0.0,
            confidence=0.0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            total_analyzed=0,
            total_pending=0
        )
        session.add(sentiment)
        commit2_start = time.perf_counter()
        session.commit()
        commit2_elapsed = time.perf_counter() - commit2_start
        logger.info(f"[WATCHLIST] add_ticker: Second commit (sentiment) in {commit2_elapsed:.3f}s")

        # Refresh to load the sentiment relationship
        logger.info("[WATCHLIST] add_ticker: Refreshing ticker...")
        session.refresh(ticker)
        _ = ticker.sentiment  # Force load relationship

        elapsed = time.perf_counter() - start
        logger.info(f"[WATCHLIST] add_ticker: Added new ticker {ticker_symbol.upper()} in {elapsed:.3f}s")
        session.expunge_all()
        return ticker


def remove_ticker(ticker_symbol: str) -> bool:
    """Remove (deactivate) a ticker from the watchlist."""
    db = get_database()
    with db.get_session() as session:
        ticker = session.query(WatchlistTicker).filter(
            WatchlistTicker.ticker == ticker_symbol.upper()
        ).first()

        if not ticker:
            return False

        ticker.is_active = False
        session.commit()
        logger.info(f"Deactivated ticker: {ticker_symbol.upper()}")
        return True


def ticker_exists(ticker_symbol: str) -> bool:
    """Check if a ticker exists in the watchlist."""
    db = get_database()
    with db.get_session() as session:
        exists = session.query(WatchlistTicker).filter(
            WatchlistTicker.ticker == ticker_symbol.upper(),
            WatchlistTicker.is_active == True
        ).first()
        return exists is not None
