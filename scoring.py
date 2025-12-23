"""Sentiment aggregation and scoring functionality."""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from models import AnalysisResult, SentimentCategory, AnalysisSummary


# Sentiment scores for aggregation
SENTIMENT_SCORES = {
    SentimentCategory.HIGHLY_NEGATIVE: -2,
    SentimentCategory.NEGATIVE: -1,
    SentimentCategory.NEUTRAL: 0,
    SentimentCategory.POSITIVE: 1,
    SentimentCategory.HIGHLY_POSITIVE: 2
}

# Reverse mapping for score to sentiment
SCORE_TO_SENTIMENT = {
    -2: "Highly Negative",
    -1: "Negative",
    0: "Neutral",
    1: "Positive",
    2: "Highly Positive"
}


@dataclass
class SentimentScore:
    """Aggregated sentiment score for a ticker."""
    ticker: str
    score: float
    normalized_score: float  # -1 to 1 scale
    sentiment_label: str
    confidence: float
    total_analyzed: int
    positive_count: int
    negative_count: int
    neutral_count: int
    time_weighted_score: Optional[float] = None
    trend: Optional[str] = None  # "improving", "declining", "stable"

    @property
    def signal(self) -> str:
        """Get trading signal based on score."""
        if self.normalized_score >= 0.5:
            return "STRONG BUY"
        elif self.normalized_score >= 0.2:
            return "BUY"
        elif self.normalized_score >= -0.2:
            return "HOLD"
        elif self.normalized_score >= -0.5:
            return "SELL"
        else:
            return "STRONG SELL"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "score": round(self.score, 3),
            "normalized_score": round(self.normalized_score, 3),
            "sentiment_label": self.sentiment_label,
            "signal": self.signal,
            "confidence": round(self.confidence, 3),
            "total_analyzed": self.total_analyzed,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "time_weighted_score": round(self.time_weighted_score, 3) if self.time_weighted_score else None,
            "trend": self.trend
        }


def calculate_sentiment_score(results: List[AnalysisResult]) -> Optional[SentimentScore]:
    """
    Calculate aggregated sentiment score from analysis results.

    Args:
        results: List of analysis results

    Returns:
        SentimentScore object or None if no valid results
    """
    if not results:
        return None

    # Filter successful results
    valid_results = [r for r in results if r.is_successful and r.analysis]

    if not valid_results:
        return None

    ticker = valid_results[0].ticker

    # Count sentiments
    positive_count = sum(
        1 for r in valid_results
        if r.analysis.sentiment in [SentimentCategory.POSITIVE, SentimentCategory.HIGHLY_POSITIVE]
    )
    negative_count = sum(
        1 for r in valid_results
        if r.analysis.sentiment in [SentimentCategory.NEGATIVE, SentimentCategory.HIGHLY_NEGATIVE]
    )
    neutral_count = sum(
        1 for r in valid_results
        if r.analysis.sentiment == SentimentCategory.NEUTRAL
    )

    # Calculate raw score
    scores = [SENTIMENT_SCORES[r.analysis.sentiment] for r in valid_results]
    avg_score = sum(scores) / len(scores)

    # Normalize to -1 to 1 scale
    normalized_score = avg_score / 2.0

    # Determine sentiment label
    if avg_score >= 1.5:
        sentiment_label = "Highly Positive"
    elif avg_score >= 0.5:
        sentiment_label = "Positive"
    elif avg_score >= -0.5:
        sentiment_label = "Neutral"
    elif avg_score >= -1.5:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Highly Negative"

    # Calculate confidence based on agreement
    from statistics import stdev
    if len(scores) > 1:
        score_std = stdev(scores)
        # Lower std = higher confidence (max std for 5 categories is ~2)
        confidence = max(0, 1 - (score_std / 2))
    else:
        confidence = 0.5  # Single result = medium confidence

    return SentimentScore(
        ticker=ticker,
        score=avg_score,
        normalized_score=normalized_score,
        sentiment_label=sentiment_label,
        confidence=confidence,
        total_analyzed=len(valid_results),
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count
    )


def calculate_time_weighted_score(
    results: List[AnalysisResult],
    decay_days: int = 7
) -> Optional[SentimentScore]:
    """
    Calculate sentiment score with time decay (more recent = more weight).

    Args:
        results: List of analysis results
        decay_days: Number of days for weight to decay by half

    Returns:
        SentimentScore with time-weighted score
    """
    base_score = calculate_sentiment_score(results)
    if not base_score:
        return None

    valid_results = [r for r in results if r.is_successful and r.analysis]
    now = datetime.now()

    weighted_sum = 0.0
    weight_total = 0.0

    for r in valid_results:
        # Calculate days since analysis
        days_old = (now - r.analyzed_at).total_seconds() / 86400

        # Exponential decay weight
        weight = 0.5 ** (days_old / decay_days)

        sentiment_value = SENTIMENT_SCORES[r.analysis.sentiment]
        weighted_sum += sentiment_value * weight
        weight_total += weight

    if weight_total > 0:
        time_weighted = weighted_sum / weight_total
        base_score.time_weighted_score = time_weighted / 2.0  # Normalize

    return base_score


def calculate_trend(
    results: List[AnalysisResult],
    window_days: int = 3
) -> Optional[SentimentScore]:
    """
    Calculate sentiment score with trend analysis.

    Args:
        results: List of analysis results
        window_days: Days to compare for trend

    Returns:
        SentimentScore with trend indicator
    """
    score = calculate_time_weighted_score(results)
    if not score or score.total_analyzed < 4:
        return score

    valid_results = [r for r in results if r.is_successful and r.analysis]
    now = datetime.now()
    cutoff = now - timedelta(days=window_days)

    # Split into recent and older
    recent = [r for r in valid_results if r.analyzed_at >= cutoff]
    older = [r for r in valid_results if r.analyzed_at < cutoff]

    if len(recent) < 2 or len(older) < 2:
        score.trend = "insufficient_data"
        return score

    # Calculate scores for each period
    recent_scores = [SENTIMENT_SCORES[r.analysis.sentiment] for r in recent]
    older_scores = [SENTIMENT_SCORES[r.analysis.sentiment] for r in older]

    recent_avg = sum(recent_scores) / len(recent_scores)
    older_avg = sum(older_scores) / len(older_scores)

    diff = recent_avg - older_avg

    if diff > 0.3:
        score.trend = "improving"
    elif diff < -0.3:
        score.trend = "declining"
    else:
        score.trend = "stable"

    return score


def get_sentiment_summary_with_score(summary: AnalysisSummary) -> Dict:
    """
    Enhance an AnalysisSummary with calculated scores.

    Args:
        summary: The analysis summary

    Returns:
        Dictionary with summary and score data
    """
    score = calculate_trend(summary.results)

    return {
        "ticker": summary.ticker,
        "total_news": summary.total_news,
        "analyzed_count": summary.analyzed_count,
        "failed_count": summary.failed_count,
        "success_rate": summary.success_rate,
        "sentiment_distribution": summary.sentiment_distribution,
        "score": score.to_dict() if score else None
    }
