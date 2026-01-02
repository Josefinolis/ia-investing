"""News sources package for multi-source news retrieval."""

from news_sources.base import NewsSource
from news_sources.alpha_vantage import AlphaVantageSource
from news_sources.reddit import RedditSource
from news_sources.twitter import TwitterSource
from news_sources.aggregator import NewsAggregator

__all__ = [
    "NewsSource",
    "AlphaVantageSource",
    "RedditSource",
    "TwitterSource",
    "NewsAggregator",
]
