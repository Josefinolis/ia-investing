"""AI-powered news sentiment analysis using Google Gemini."""

import json
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import get_settings
from models import SentimentAnalysis
from logger import logger, log_api_call, log_error

# Module-level client (initialized lazily)
_client: Optional[genai.Client] = None


class AnalysisError(Exception):
    """Custom exception for analysis errors."""
    pass


def _get_client() -> genai.Client:
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        try:
            _client = genai.Client()
            logger.debug("Gemini client initialized successfully")
        except Exception as e:
            log_error("Failed to initialize Gemini client", e)
            raise AnalysisError(
                "Could not initialize Gemini client. "
                "Ensure GEMINI_API_KEY is set in your .env file."
            )
    return _client


@sleep_and_retry
@limits(calls=15, period=60)
def _rate_limited_generate(
    client: genai.Client,
    model: str,
    prompt: str,
    config: types.GenerateContentConfig
) -> Any:
    """Make a rate-limited Gemini API call."""
    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((AnalysisError,)),
    before_sleep=lambda retry_state: logger.debug(
        f"Retry attempt {retry_state.attempt_number} for Gemini API"
    )
)
def analyze_sentiment(
    ticker: str,
    news_text: str
) -> Optional[SentimentAnalysis]:
    """
    Analyze news sentiment using Gemini AI.

    Args:
        ticker: Stock ticker symbol for context
        news_text: News text to analyze

    Returns:
        SentimentAnalysis object if successful, None otherwise
    """
    settings = get_settings()
    client = _get_client()

    prompt = _build_prompt(ticker, news_text)

    config = types.GenerateContentConfig(
        response_mime_type="application/json"
    )

    try:
        log_api_call("Gemini", f"sentiment analysis for {ticker}")
        response = _rate_limited_generate(
            client,
            settings.gemini_model,
            prompt,
            config
        )

        result = json.loads(response.text)
        return SentimentAnalysis(**result)

    except json.JSONDecodeError as e:
        log_error("Gemini returned invalid JSON", e)
        return None

    except Exception as e:
        log_error("Gemini API call failed", e)
        return None


def _build_prompt(ticker: str, news_text: str) -> str:
    """Build the analysis prompt."""
    return f"""Act as a quantitative market analyst specialized in short-term trading.
Evaluate the news text provided about the stock {ticker} to classify its sentiment and potential short-term price impact.

Format the response strictly as a JSON object with two fields:
1. "SENTIMENT" (Use only one of these categories: 'Highly Negative', 'Negative', 'Neutral', 'Positive', 'Highly Positive').
2. "JUSTIFICATION" (A concise 1-2 sentence summary explaining the main reason for the impact).

TEXT TO ANALYZE:
---
{news_text}
---
"""


# Backwards compatibility alias
def analyze_news_with_gemini(ticker: str, news_text: str) -> Optional[Dict[str, Any]]:
    """Backwards compatible wrapper for analyze_sentiment."""
    result = analyze_sentiment(ticker, news_text)
    if result:
        return {
            "SENTIMENT": result.sentiment.value,
            "JUSTIFICATION": result.justification
        }
    return None
