"""Sentiment aggregation service."""

from typing import Optional
from datetime import datetime
from sqlalchemy import func

from database import TickerSentiment, NewsRecord, get_database
from models import SentimentCategory
from logger import logger


# Sentiment score mapping
SENTIMENT_SCORES = {
    SentimentCategory.HIGHLY_POSITIVE.value: 1.0,
    SentimentCategory.POSITIVE.value: 0.5,
    SentimentCategory.NEUTRAL.value: 0.0,
    SentimentCategory.NEGATIVE.value: -0.5,
    SentimentCategory.HIGHLY_NEGATIVE.value: -1.0,
}


def get_ticker_sentiment(ticker_symbol: str) -> Optional[TickerSentiment]:
    """Get aggregated sentiment for a ticker."""
    db = get_database()
    with db.get_session() as session:
        sentiment = session.query(TickerSentiment).filter(
            TickerSentiment.ticker == ticker_symbol.upper()
        ).first()
        if sentiment:
            session.expunge(sentiment)
        return sentiment


def update_ticker_sentiment(ticker_symbol: str) -> Optional[TickerSentiment]:
    """Recalculate and update aggregated sentiment for a ticker."""
    db = get_database()
    with db.get_session() as session:
        # Get or create sentiment record
        sentiment = session.query(TickerSentiment).filter(
            TickerSentiment.ticker == ticker_symbol.upper()
        ).first()

        if not sentiment:
            sentiment = TickerSentiment(
                ticker=ticker_symbol.upper()
            )
            session.add(sentiment)

        # Count news by status
        pending_count = session.query(func.count(NewsRecord.id)).filter(
            NewsRecord.ticker == ticker_symbol.upper(),
            NewsRecord.status == "pending"
        ).scalar() or 0

        # Get analyzed news with sentiment
        analyzed_news = session.query(NewsRecord).filter(
            NewsRecord.ticker == ticker_symbol.upper(),
            NewsRecord.status == "analyzed",
            NewsRecord.sentiment.isnot(None)
        ).all()

        # Count sentiments
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_score = 0.0

        for news in analyzed_news:
            score = SENTIMENT_SCORES.get(news.sentiment, 0.0)
            total_score += score

            if score > 0:
                positive_count += 1
            elif score < 0:
                negative_count += 1
            else:
                neutral_count += 1

        total_analyzed = len(analyzed_news)

        # Calculate normalized score (-1 to 1)
        if total_analyzed > 0:
            normalized_score = total_score / total_analyzed
        else:
            normalized_score = 0.0

        # Determine sentiment label
        if normalized_score >= 0.5:
            sentiment_label = SentimentCategory.HIGHLY_POSITIVE.value
        elif normalized_score >= 0.2:
            sentiment_label = SentimentCategory.POSITIVE.value
        elif normalized_score >= -0.2:
            sentiment_label = SentimentCategory.NEUTRAL.value
        elif normalized_score >= -0.5:
            sentiment_label = SentimentCategory.NEGATIVE.value
        else:
            sentiment_label = SentimentCategory.HIGHLY_NEGATIVE.value

        # Determine trading signal
        if normalized_score >= 0.5:
            signal = "STRONG BUY"
        elif normalized_score >= 0.2:
            signal = "BUY"
        elif normalized_score >= -0.2:
            signal = "HOLD"
        elif normalized_score >= -0.5:
            signal = "SELL"
        else:
            signal = "STRONG SELL"

        # Calculate confidence (based on agreement)
        if total_analyzed > 0:
            max_count = max(positive_count, negative_count, neutral_count)
            confidence = max_count / total_analyzed
        else:
            confidence = 0.0

        # Update sentiment record
        sentiment.score = total_score
        sentiment.normalized_score = round(normalized_score, 4)
        sentiment.sentiment_label = sentiment_label
        sentiment.signal = signal
        sentiment.confidence = round(confidence, 4)
        sentiment.positive_count = positive_count
        sentiment.negative_count = negative_count
        sentiment.neutral_count = neutral_count
        sentiment.total_analyzed = total_analyzed
        sentiment.total_pending = pending_count
        sentiment.updated_at = datetime.now()

        session.commit()
        logger.info(
            f"Updated sentiment for {ticker_symbol}: "
            f"score={normalized_score:.2f}, signal={signal}"
        )

        session.expunge(sentiment)
        return sentiment
