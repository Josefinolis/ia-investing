"""News aggregator that combines multiple news sources."""

from datetime import datetime
from typing import List, Optional, Set
from difflib import SequenceMatcher

from news_sources.base import NewsSource
from news_sources.alpha_vantage import AlphaVantageSource
from news_sources.reddit import RedditSource
from news_sources.twitter import TwitterSource
from models import NewsItem
from logger import logger


class NewsAggregator:
    """Aggregates news from multiple sources with deduplication."""

    def __init__(
        self,
        sources: Optional[List[NewsSource]] = None,
        similarity_threshold: float = 0.85,
    ):
        """
        Initialize the news aggregator.

        Args:
            sources: List of NewsSource instances. If None, uses all available sources.
            similarity_threshold: Threshold for title similarity deduplication (0-1)
        """
        if sources is None:
            sources = self._get_default_sources()

        self.sources = [s for s in sources if s.is_available()]
        self.similarity_threshold = similarity_threshold

        available_names = [s.source_name for s in self.sources]
        logger.info(f"NewsAggregator initialized with sources: {available_names}")

    def _get_default_sources(self) -> List[NewsSource]:
        """Get all default news sources."""
        return [
            AlphaVantageSource(),
            RedditSource(),
            TwitterSource(),
        ]

    def fetch_all(
        self,
        ticker: str,
        time_from: datetime,
        time_to: datetime,
        sources_filter: Optional[List[str]] = None,
    ) -> List[NewsItem]:
        """
        Fetch news from all available sources.

        Args:
            ticker: Stock ticker symbol
            time_from: Start datetime
            time_to: End datetime
            sources_filter: Optional list of source names to use (e.g., ["alpha_vantage", "reddit"])

        Returns:
            Deduplicated list of NewsItem objects sorted by date
        """
        all_news: List[NewsItem] = []
        sources_to_use = self.sources

        if sources_filter:
            sources_to_use = [
                s for s in self.sources if s.source_name in sources_filter
            ]
            if not sources_to_use:
                logger.warning(
                    f"No sources match filter {sources_filter}, using all available"
                )
                sources_to_use = self.sources

        for source in sources_to_use:
            try:
                logger.debug(f"Fetching news from {source.source_name}")
                news = source.fetch_news(ticker, time_from, time_to)
                all_news.extend(news)
                logger.debug(f"Got {len(news)} items from {source.source_name}")

            except Exception as e:
                logger.warning(f"Error fetching from {source.source_name}: {e}")
                continue

        deduplicated = self._deduplicate(all_news)
        sorted_news = self._sort_by_date(deduplicated)

        logger.info(
            f"Aggregated {len(sorted_news)} news items for {ticker} "
            f"(from {len(all_news)} raw items)"
        )

        return sorted_news

    def _deduplicate(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate news items based on URL and title similarity."""
        if not news_items:
            return []

        unique_items: List[NewsItem] = []
        seen_urls: Set[str] = set()

        for item in news_items:
            if item.url and item.url in seen_urls:
                continue

            is_duplicate = False
            for existing in unique_items:
                if self._is_similar(item.title, existing.title):
                    if self._get_priority(item) > self._get_priority(existing):
                        unique_items.remove(existing)
                        if existing.url:
                            seen_urls.discard(existing.url)
                    else:
                        is_duplicate = True
                    break

            if not is_duplicate:
                unique_items.append(item)
                if item.url:
                    seen_urls.add(item.url)

        return unique_items

    def _is_similar(self, title1: str, title2: str) -> bool:
        """Check if two titles are similar enough to be duplicates."""
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        if t1 == t2:
            return True

        ratio = SequenceMatcher(None, t1, t2).ratio()
        return ratio >= self.similarity_threshold

    def _get_priority(self, item: NewsItem) -> int:
        """
        Get priority score for a news item.
        Higher priority items are preferred when deduplicating.
        """
        source_priorities = {
            "alpha_vantage": 3,
            "reddit": 2,
            "twitter": 1,
        }

        priority = source_priorities.get(item.source_type or "", 0)

        if item.relevance_score:
            priority += item.relevance_score

        return priority

    def _sort_by_date(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Sort news items by published date (newest first)."""
        def parse_date(item: NewsItem) -> datetime:
            try:
                date_str = item.published_date
                for fmt in ["%Y%m%dT%H%M%S", "%Y%m%dT%H%M", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                return datetime.min
            except Exception:
                return datetime.min

        return sorted(news_items, key=parse_date, reverse=True)

    def get_available_sources(self) -> List[str]:
        """Get list of available source names."""
        return [s.source_name for s in self.sources]


def get_aggregator() -> NewsAggregator:
    """Get a default NewsAggregator instance."""
    return NewsAggregator()
