"""Watchlist management service."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database import WatchlistTicker, TickerSentiment, get_database
from logger import logger


def get_all_tickers(include_inactive: bool = False) -> List[WatchlistTicker]:
    """Get all tickers from watchlist."""
    db = get_database()
    with db.get_session() as session:
        query = session.query(WatchlistTicker)
        if not include_inactive:
            query = query.filter(WatchlistTicker.is_active == True)
        tickers = query.order_by(WatchlistTicker.added_at.desc()).all()
        # Eagerly load relationships before session closes
        for ticker in tickers:
            _ = ticker.sentiment  # Force load
        session.expunge_all()
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
    db = get_database()
    with db.get_session() as session:
        # Check if ticker already exists
        existing = session.query(WatchlistTicker).filter(
            WatchlistTicker.ticker == ticker_symbol.upper()
        ).first()

        if existing:
            # Reactivate if inactive
            if not existing.is_active:
                existing.is_active = True
                if name:
                    existing.name = name
                session.commit()
                logger.info(f"Reactivated ticker: {ticker_symbol.upper()}")
            _ = existing.sentiment  # Force load relationship
            session.expunge_all()
            return existing

        # Create new ticker
        ticker = WatchlistTicker(
            ticker=ticker_symbol.upper(),
            name=name,
            added_at=datetime.now(),
            is_active=True
        )
        session.add(ticker)
        session.commit()

        # Create empty sentiment record
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
        session.commit()

        # Refresh to load the sentiment relationship
        session.refresh(ticker)
        _ = ticker.sentiment  # Force load relationship

        logger.info(f"Added ticker to watchlist: {ticker_symbol.upper()}")
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
