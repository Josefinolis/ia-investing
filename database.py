"""SQLite database persistence for analysis results."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config import get_settings
from models import SentimentCategory, AnalysisResult, NewsItem, SentimentAnalysis
from logger import logger

Base = declarative_base()


class AnalysisRecord(Base):
    """Database model for storing analysis results."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    published_date = Column(String(50))
    source = Column(String(200))
    url = Column(String(500))
    relevance_score = Column(Float)
    sentiment = Column(String(20))
    justification = Column(Text)
    analyzed_at = Column(DateTime, default=datetime.now, index=True)
    error = Column(Text)

    def to_analysis_result(self) -> AnalysisResult:
        """Convert database record to AnalysisResult model."""
        news = NewsItem(
            title=self.title,
            summary=self.summary,
            published_date=self.published_date or "",
            source=self.source,
            url=self.url,
            relevance_score=self.relevance_score
        )

        analysis = None
        if self.sentiment:
            try:
                analysis = SentimentAnalysis(
                    SENTIMENT=SentimentCategory(self.sentiment),
                    JUSTIFICATION=self.justification or ""
                )
            except ValueError:
                pass

        return AnalysisResult(
            news=news,
            analysis=analysis,
            analyzed_at=self.analyzed_at or datetime.now(),
            ticker=self.ticker,
            error=self.error
        )


class Database:
    """Database manager for analysis results."""

    def __init__(self, database_url: Optional[str] = None):
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def init_db(self):
        """Create database tables."""
        Base.metadata.create_all(self.engine)
        logger.debug("Database tables initialized")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_result(self, result: AnalysisResult) -> int:
        """
        Save an analysis result to the database.

        Returns:
            The ID of the saved record
        """
        record = AnalysisRecord(
            ticker=result.ticker,
            title=result.news.title,
            summary=result.news.summary,
            published_date=result.news.published_date,
            source=result.news.source,
            url=result.news.url,
            relevance_score=result.news.relevance_score,
            sentiment=result.analysis.sentiment.value if result.analysis else None,
            justification=result.analysis.justification if result.analysis else None,
            analyzed_at=result.analyzed_at,
            error=result.error
        )

        with self.get_session() as session:
            session.add(record)
            session.commit()
            logger.debug(f"Saved analysis result with ID {record.id}")
            return record.id

    def save_results(self, results: List[AnalysisResult]) -> List[int]:
        """Save multiple analysis results."""
        ids = []
        for result in results:
            record_id = self.save_result(result)
            ids.append(record_id)
        return ids

    def get_results_by_ticker(
        self,
        ticker: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AnalysisResult]:
        """Get analysis results for a specific ticker."""
        with self.get_session() as session:
            records = (
                session.query(AnalysisRecord)
                .filter(AnalysisRecord.ticker == ticker.upper())
                .order_by(AnalysisRecord.analyzed_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            return [r.to_analysis_result() for r in records]

    def get_results_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        ticker: Optional[str] = None
    ) -> List[AnalysisResult]:
        """Get analysis results within a date range."""
        with self.get_session() as session:
            query = session.query(AnalysisRecord).filter(
                AnalysisRecord.analyzed_at >= start_date,
                AnalysisRecord.analyzed_at <= end_date
            )

            if ticker:
                query = query.filter(AnalysisRecord.ticker == ticker.upper())

            records = query.order_by(AnalysisRecord.analyzed_at.desc()).all()
            return [r.to_analysis_result() for r in records]

    def get_sentiment_summary(self, ticker: str) -> dict:
        """Get sentiment distribution summary for a ticker."""
        with self.get_session() as session:
            records = (
                session.query(AnalysisRecord)
                .filter(AnalysisRecord.ticker == ticker.upper())
                .filter(AnalysisRecord.sentiment.isnot(None))
                .all()
            )

            distribution = {}
            for category in SentimentCategory:
                distribution[category.value] = 0

            for record in records:
                if record.sentiment in distribution:
                    distribution[record.sentiment] += 1

            return {
                "ticker": ticker.upper(),
                "total_analyzed": len(records),
                "distribution": distribution
            }

    def check_duplicate(self, ticker: str, title: str) -> bool:
        """Check if a news item has already been analyzed."""
        with self.get_session() as session:
            exists = (
                session.query(AnalysisRecord)
                .filter(
                    AnalysisRecord.ticker == ticker.upper(),
                    AnalysisRecord.title == title
                )
                .first()
            )
            return exists is not None


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = Database()
        _db.init_db()
    return _db
