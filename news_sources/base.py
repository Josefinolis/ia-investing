"""Base class for news sources."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from models import NewsItem


class NewsSource(ABC):
    """Abstract base class for all news sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this news source."""
        pass

    @abstractmethod
    def fetch_news(
        self,
        ticker: str,
        time_from: datetime,
        time_to: datetime,
    ) -> List[NewsItem]:
        """
        Fetch news items from this source.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            time_from: Start datetime for news search
            time_to: End datetime for news search

        Returns:
            List of NewsItem objects
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this news source is configured and available.

        Returns:
            True if the source can be used, False otherwise
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(available={self.is_available()})>"
