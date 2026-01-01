"""News management service."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import NewsRecord, get_database
from models import NewsItem
from logger import logger


def get_news_by_ticker(
    ticker_symbol: str,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[NewsRecord]:
    """Get news items for a ticker."""
    db = get_database()
    with db.get_session() as session:
        query = session.query(NewsRecord).filter(
            NewsRecord.ticker == ticker_symbol.upper()
        )

        if status:
            query = query.filter(NewsRecord.status == status)

        news = (
            query
            .order_by(NewsRecord.fetched_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        session.expunge_all()
        return news


def get_news_counts(ticker_symbol: str) -> dict:
    """Get count of pending and analyzed news for a ticker."""
    db = get_database()
    with db.get_session() as session:
        pending = session.query(func.count(NewsRecord.id)).filter(
            NewsRecord.ticker == ticker_symbol.upper(),
            NewsRecord.status == "pending"
        ).scalar()

        analyzed = session.query(func.count(NewsRecord.id)).filter(
            NewsRecord.ticker == ticker_symbol.upper(),
            NewsRecord.status == "analyzed"
        ).scalar()

        return {
            "pending": pending or 0,
            "analyzed": analyzed or 0,
            "total": (pending or 0) + (analyzed or 0)
        }


def save_news_item(
    ticker_symbol: str,
    news: NewsItem
) -> Optional[NewsRecord]:
    """Save a news item to the database if not duplicate."""
    db = get_database()
    with db.get_session() as session:
        # Check for duplicate by URL
        if news.url:
            existing = session.query(NewsRecord).filter(
                NewsRecord.url == news.url
            ).first()
            if existing:
                logger.debug(f"Skipping duplicate news: {news.url}")
                return None

        record = NewsRecord(
            ticker=ticker_symbol.upper(),
            title=news.title,
            summary=news.summary,
            published_date=news.published_date,
            source=news.source,
            url=news.url,
            relevance_score=news.relevance_score,
            status="pending",
            fetched_at=datetime.now()
        )

        session.add(record)
        session.commit()
        logger.debug(f"Saved news item: {news.title[:50]}...")
        session.expunge(record)
        return record


def save_news_items(
    ticker_symbol: str,
    news_list: List[NewsItem]
) -> int:
    """Save multiple news items, returns count of saved items."""
    saved_count = 0
    for news in news_list:
        result = save_news_item(ticker_symbol, news)
        if result:
            saved_count += 1
    logger.info(f"Saved {saved_count}/{len(news_list)} news items for {ticker_symbol}")
    return saved_count


def get_pending_news(limit: int = 10) -> List[NewsRecord]:
    """Get pending news items for analysis."""
    db = get_database()
    with db.get_session() as session:
        news = (
            session.query(NewsRecord)
            .filter(NewsRecord.status == "pending")
            .order_by(NewsRecord.fetched_at.asc())  # Oldest first
            .limit(limit)
            .all()
        )
        session.expunge_all()
        return news


def get_pending_news_for_ticker(ticker_symbol: str, limit: int = 100) -> List[NewsRecord]:
    """Get pending news items for a specific ticker."""
    db = get_database()
    with db.get_session() as session:
        news = (
            session.query(NewsRecord)
            .filter(
                NewsRecord.ticker == ticker_symbol.upper(),
                NewsRecord.status == "pending"
            )
            .order_by(NewsRecord.fetched_at.asc())
            .limit(limit)
            .all()
        )
        session.expunge_all()
        return news


def update_news_analysis(
    news_id: int,
    sentiment: str,
    justification: str
) -> bool:
    """Update a news item with analysis results."""
    db = get_database()
    with db.get_session() as session:
        news = session.query(NewsRecord).filter(
            NewsRecord.id == news_id
        ).first()

        if not news:
            return False

        news.sentiment = sentiment
        news.justification = justification
        news.status = "analyzed"
        news.analyzed_at = datetime.now()

        session.commit()
        logger.debug(f"Updated news analysis: {news_id} -> {sentiment}")
        return True
