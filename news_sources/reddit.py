"""Reddit news source implementation using PRAW."""

import re
from datetime import datetime, timezone
from typing import List, Optional

from news_sources.base import NewsSource
from models import NewsItem
from config import get_settings
from logger import logger

# Default subreddits for stock/trading news
DEFAULT_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "stockmarket", "options"]


class RedditSource(NewsSource):
    """News source using Reddit API via PRAW."""

    def __init__(
        self,
        subreddits: Optional[List[str]] = None,
        min_score: int = 10,
        limit_per_subreddit: int = 25,
    ):
        """
        Initialize Reddit source.

        Args:
            subreddits: List of subreddit names to search
            min_score: Minimum post score (upvotes - downvotes)
            limit_per_subreddit: Max posts to fetch per subreddit
        """
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.min_score = min_score
        self.limit_per_subreddit = limit_per_subreddit
        self._reddit = None

    @property
    def source_name(self) -> str:
        return "reddit"

    def is_available(self) -> bool:
        """Check if Reddit credentials are configured."""
        settings = get_settings()
        return bool(
            getattr(settings, "reddit_client_id", None)
            and getattr(settings, "reddit_client_secret", None)
        )

    def _get_reddit_client(self):
        """Get or create Reddit client."""
        if self._reddit is None:
            try:
                import praw

                settings = get_settings()
                self._reddit = praw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=getattr(
                        settings, "reddit_user_agent", "ia_trading/1.0"
                    ),
                )
            except ImportError:
                logger.error("praw library not installed. Run: pip install praw")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Reddit client: {e}")
                raise

        return self._reddit

    def fetch_news(
        self,
        ticker: str,
        time_from: datetime,
        time_to: datetime,
    ) -> List[NewsItem]:
        """
        Fetch posts from Reddit mentioning the ticker.

        Args:
            ticker: Stock ticker symbol
            time_from: Start datetime
            time_to: End datetime

        Returns:
            List of NewsItem objects
        """
        if not self.is_available():
            logger.warning("Reddit credentials not configured, skipping Reddit source")
            return []

        try:
            reddit = self._get_reddit_client()
        except Exception as e:
            logger.error(f"Failed to get Reddit client: {e}")
            return []

        news_items: List[NewsItem] = []
        search_terms = self._build_search_terms(ticker)

        time_from_utc = time_from.replace(tzinfo=timezone.utc)
        time_to_utc = time_to.replace(tzinfo=timezone.utc)

        for subreddit_name in self.subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                logger.debug(f"Searching r/{subreddit_name} for {ticker}")

                for search_term in search_terms:
                    try:
                        submissions = subreddit.search(
                            search_term,
                            sort="relevance",
                            time_filter="month",
                            limit=self.limit_per_subreddit,
                        )

                        for submission in submissions:
                            created_utc = datetime.fromtimestamp(
                                submission.created_utc, tz=timezone.utc
                            )

                            if created_utc < time_from_utc or created_utc > time_to_utc:
                                continue

                            if submission.score < self.min_score:
                                continue

                            if self._is_meme_post(submission):
                                continue

                            news_item = self._submission_to_news_item(
                                submission, ticker
                            )
                            if news_item and not self._is_duplicate(
                                news_item, news_items
                            ):
                                news_items.append(news_item)

                    except Exception as e:
                        logger.warning(
                            f"Error searching '{search_term}' in r/{subreddit_name}: {e}"
                        )
                        continue

            except Exception as e:
                logger.warning(f"Error accessing r/{subreddit_name}: {e}")
                continue

        logger.info(f"Retrieved {len(news_items)} posts from Reddit for {ticker}")
        return news_items

    def _build_search_terms(self, ticker: str) -> List[str]:
        """Build search terms for a ticker."""
        return [
            f"${ticker}",
            ticker,
        ]

    def _is_meme_post(self, submission) -> bool:
        """Check if a post is likely a meme/shitpost."""
        meme_flairs = ["meme", "shitpost", "yolo", "gain", "loss", "daily discussion"]
        flair = (submission.link_flair_text or "").lower()
        return any(meme_flair in flair for meme_flair in meme_flairs)

    def _submission_to_news_item(self, submission, ticker: str) -> Optional[NewsItem]:
        """Convert a Reddit submission to a NewsItem."""
        try:
            title = submission.title.strip()
            if len(title) > 500:
                title = title[:497] + "..."

            selftext = submission.selftext or ""
            if len(selftext) > 2000:
                selftext = selftext[:1997] + "..."

            summary = selftext if selftext else f"Reddit post discussing {ticker}"
            if not summary.strip():
                summary = f"Reddit post: {title}"

            created_utc = datetime.fromtimestamp(
                submission.created_utc, tz=timezone.utc
            )
            published_date = created_utc.strftime("%Y%m%dT%H%M%S")

            max_score = 10000
            relevance_score = min(submission.score / max_score, 1.0)

            return NewsItem(
                title=title,
                summary=summary,
                published_date=published_date,
                source=f"r/{submission.subreddit.display_name}",
                source_type="reddit",
                url=f"https://reddit.com{submission.permalink}",
                relevance_score=round(relevance_score, 4),
                engagement_score=submission.score,
                author=str(submission.author) if submission.author else None,
            )

        except Exception as e:
            logger.warning(f"Error converting Reddit submission: {e}")
            return None

    def _is_duplicate(
        self, news_item: NewsItem, existing_items: List[NewsItem]
    ) -> bool:
        """Check if a news item is a duplicate."""
        for existing in existing_items:
            if existing.url == news_item.url:
                return True
            if existing.title.lower() == news_item.title.lower():
                return True
        return False
