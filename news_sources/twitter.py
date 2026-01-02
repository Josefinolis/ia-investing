"""Twitter/X news source implementation using ntscraper."""

from datetime import datetime, timezone
from typing import List, Optional

from news_sources.base import NewsSource
from models import NewsItem
from config import get_settings
from logger import logger


class TwitterSource(NewsSource):
    """News source using Twitter/X via ntscraper (scraping)."""

    def __init__(
        self,
        min_likes: int = 10,
        min_retweets: int = 5,
        max_results: int = 50,
        include_replies: bool = False,
    ):
        """
        Initialize Twitter source.

        Args:
            min_likes: Minimum likes to include a tweet
            min_retweets: Minimum retweets to include
            max_results: Maximum tweets to fetch
            include_replies: Whether to include reply tweets
        """
        self.min_likes = min_likes
        self.min_retweets = min_retweets
        self.max_results = max_results
        self.include_replies = include_replies
        self._scraper = None
        self._available = None

    @property
    def source_name(self) -> str:
        return "twitter"

    def is_available(self) -> bool:
        """Check if ntscraper is installed and working."""
        if self._available is not None:
            return self._available

        settings = get_settings()
        if not getattr(settings, "twitter_enabled", True):
            self._available = False
            return False

        try:
            from ntscraper import Nitter

            self._available = True
        except ImportError:
            logger.warning("ntscraper not installed. Run: pip install ntscraper")
            self._available = False
        except Exception as e:
            logger.warning(f"ntscraper initialization error: {e}")
            self._available = False

        return self._available

    def _get_scraper(self):
        """Get or create Nitter scraper."""
        if self._scraper is None:
            try:
                from ntscraper import Nitter

                self._scraper = Nitter(log_level=1)
            except Exception as e:
                logger.error(f"Failed to create Nitter scraper: {e}")
                raise

        return self._scraper

    def fetch_news(
        self,
        ticker: str,
        time_from: datetime,
        time_to: datetime,
    ) -> List[NewsItem]:
        """
        Fetch tweets mentioning the ticker.

        Args:
            ticker: Stock ticker symbol
            time_from: Start datetime
            time_to: End datetime

        Returns:
            List of NewsItem objects
        """
        if not self.is_available():
            logger.warning("Twitter source not available, skipping")
            return []

        news_items: List[NewsItem] = []

        try:
            scraper = self._get_scraper()
        except Exception as e:
            logger.error(f"Failed to get scraper: {e}")
            return []

        search_terms = [f"${ticker}", f"#{ticker}"]

        for search_term in search_terms:
            try:
                logger.debug(f"Searching Twitter for: {search_term}")

                tweets = scraper.get_tweets(
                    search_term,
                    mode="term",
                    number=self.max_results // len(search_terms),
                )

                if not tweets or "tweets" not in tweets:
                    continue

                for tweet_data in tweets["tweets"]:
                    try:
                        news_item = self._parse_tweet(tweet_data, ticker, time_from, time_to)
                        if news_item and not self._is_duplicate(news_item, news_items):
                            news_items.append(news_item)
                    except Exception as e:
                        logger.debug(f"Error parsing tweet: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Error searching Twitter for '{search_term}': {e}")
                continue

        logger.info(f"Retrieved {len(news_items)} tweets for {ticker}")
        return news_items

    def _parse_tweet(
        self,
        tweet_data: dict,
        ticker: str,
        time_from: datetime,
        time_to: datetime,
    ) -> Optional[NewsItem]:
        """Parse tweet data into NewsItem."""
        try:
            # Parse date
            date_str = tweet_data.get("date", "")
            tweet_date = self._parse_date(date_str)

            if tweet_date:
                # Make time_from and time_to timezone-aware if they aren't
                tf = time_from.replace(tzinfo=timezone.utc) if time_from.tzinfo is None else time_from
                tt = time_to.replace(tzinfo=timezone.utc) if time_to.tzinfo is None else time_to

                if tweet_date < tf or tweet_date > tt:
                    return None

            # Get engagement stats
            stats = tweet_data.get("stats", {})
            likes = self._parse_stat(stats.get("likes", "0"))
            retweets = self._parse_stat(stats.get("retweets", "0"))
            engagement = likes + retweets

            # Filter by engagement
            if likes < self.min_likes and retweets < self.min_retweets:
                return None

            # Skip replies if configured
            if not self.include_replies and tweet_data.get("is-retweet"):
                return None

            # Get content
            text = tweet_data.get("text", "")
            if not text.strip():
                return None

            title = text[:100] + "..." if len(text) > 100 else text
            title = title.replace("\n", " ").strip()

            if len(title) > 500:
                title = title[:497] + "..."

            summary = text
            if len(summary) > 2000:
                summary = summary[:1997] + "..."

            # Build published date string
            published_date = tweet_date.strftime("%Y%m%dT%H%M%S") if tweet_date else "Unknown"

            # Calculate relevance score
            max_engagement = 10000
            relevance_score = min(engagement / max_engagement, 1.0)

            # Get author info
            user = tweet_data.get("user", {})
            author = user.get("username") if isinstance(user, dict) else None

            # Build URL
            link = tweet_data.get("link", "")
            url = f"https://twitter.com{link}" if link and not link.startswith("http") else link

            return NewsItem(
                title=title,
                summary=summary,
                published_date=published_date,
                source="Twitter/X",
                source_type="twitter",
                url=url or None,
                relevance_score=round(relevance_score, 4),
                engagement_score=engagement,
                author=f"@{author}" if author else None,
                author_followers=None,
            )

        except Exception as e:
            logger.debug(f"Error converting tweet: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string from ntscraper."""
        if not date_str:
            return None

        # ntscraper returns dates like "Jan 1, 2026 · 10:30 AM UTC"
        formats = [
            "%b %d, %Y · %I:%M %p UTC",
            "%b %d, %Y · %H:%M UTC",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        # Try to extract just the date part
        try:
            import re
            match = re.search(r"(\w+ \d+, \d+)", date_str)
            if match:
                dt = datetime.strptime(match.group(1), "%b %d, %Y")
                return dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass

        return None

    def _parse_stat(self, stat_str: str) -> int:
        """Parse stat string like '1.2K' to integer."""
        if not stat_str:
            return 0

        stat_str = str(stat_str).strip().upper()

        try:
            if "K" in stat_str:
                return int(float(stat_str.replace("K", "")) * 1000)
            elif "M" in stat_str:
                return int(float(stat_str.replace("M", "")) * 1000000)
            else:
                return int(stat_str.replace(",", ""))
        except (ValueError, TypeError):
            return 0

    def _is_duplicate(
        self, news_item: NewsItem, existing_items: List[NewsItem]
    ) -> bool:
        """Check if a news item is a duplicate."""
        for existing in existing_items:
            if existing.url and news_item.url and existing.url == news_item.url:
                return True
        return False
