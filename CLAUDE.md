# IA Trading - Market Sentiment Analysis Tool

## Project Overview

**IA Trading** is a Python-based market sentiment analysis tool that leverages AI to analyze news sentiment for publicly traded companies. The tool retrieves financial news for specific tickers and uses Google's Gemini AI to classify sentiment and identify potential trading opportunities.

### Purpose
- Retrieve real-time and historical news data for stock tickers via Alpha Vantage API
- Analyze news sentiment using Google Gemini AI (gemini-2.5-flash model)
- Classify sentiment into 5 categories: Highly Negative, Negative, Neutral, Positive, Highly Positive
- Provide actionable justifications for sentiment classifications to inform trading decisions

### Current Status
This is an early-stage prototype (~172 lines of code across 4 Python modules). The core functionality works but lacks production-readiness features like error handling, testing, logging, data persistence, and security best practices.

---

## Architecture & Key Components

### System Architecture

```
┌─────────────────┐
│    main.py      │  Entry point - orchestrates workflow
└────────┬────────┘
         │
         ├──────────────────────────────────┐
         │                                  │
         v                                  v
┌────────────────────┐          ┌──────────────────────┐
│ news_retriever.py  │          │   ia_analisis.py     │
│                    │          │                      │
│ - Alpha Vantage    │          │ - Gemini AI Client   │
│   API Integration  │          │ - Sentiment Analysis │
│ - News Fetching    │          │ - JSON Response      │
└────────┬───────────┘          └──────────────────────┘
         │
         v
┌────────────────────┐
│     news.py        │
│                    │
│ - News Data Model  │
└────────────────────┘
```

### Component Details

#### 1. **main.py** - Application Entry Point
- **Responsibilities**:
  - Orchestrates the end-to-end workflow
  - Defines ticker symbol and date range
  - Fetches news data via `news_retriever`
  - Sends news to AI analysis via `ia_analisis`
  - Formats and displays results to console
- **Key Functions**: None (procedural script)
- **Current Limitations**:
  - Hardcoded ticker ("ASTS") and date range
  - No command-line argument parsing
  - No output persistence (console only)
  - No batch processing capability
  - Hardcoded date in line 11 (2025, 10, 20) appears to be a future date typo

#### 2. **news_retriever.py** - News Data Pipeline
- **Responsibilities**:
  - Constructs Alpha Vantage API requests
  - Fetches news data via HTTP
  - Parses and validates JSON responses
  - Transforms raw API data into News objects
- **Key Functions**:
  - `get_news_data(ticker, time_from, time_to)` - Main entry point
  - `fetch_raw_data()` - HTTP request handler
  - `build_url()` - URL construction with API key
  - `process_api_response()` - JSON to News object transformation
- **Strengths**:
  - Good separation of concerns (fetch vs. process)
  - Type hints throughout
  - Basic error handling for HTTP and JSON errors
- **Current Limitations**:
  - No retry logic for failed API calls
  - No rate limiting handling (Alpha Vantage has strict limits)
  - No caching of API responses
  - API key loaded from environment but not validated

#### 3. **ia_analisis.py** - AI Sentiment Analysis
- **Responsibilities**:
  - Initialize Google Gemini AI client
  - Construct analysis prompts
  - Execute sentiment classification
  - Parse and return structured JSON results
- **Key Functions**:
  - `analyze_news_with_gemini(ticker, news_text)` - Performs sentiment analysis
- **Strengths**:
  - Structured JSON output with defined schema
  - Clear prompt engineering for consistent results
  - Basic error handling for API failures
- **Current Limitations**:
  - Client initialization failure causes hard exit (no graceful degradation)
  - No prompt versioning or A/B testing capability
  - No validation of Gemini response schema
  - No cost tracking or token usage monitoring
  - Hardcoded model name ('gemini-2.5-flash')

#### 4. **news.py** - Data Model
- **Responsibilities**:
  - Define News data structure
  - Provide string representation
- **Key Classes**:
  - `News(title, published_date, summary)` - Simple data class
- **Current Limitations**:
  - Not using Python dataclasses or Pydantic for validation
  - No date parsing or validation
  - No sentiment storage (results not attached to News objects)
  - Limited metadata (missing source, URL, relevance score, etc.)

---

## Setup and Installation

### Prerequisites
- Python 3.12+ (tested on Python 3.12)
- Alpha Vantage API Key (free tier available at https://www.alphavantage.co)
- Google Gemini API Key (available at https://aistudio.google.com/apikey)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ia_trading
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Core dependencies:
   - `google-genai==1.52.0` - Google Gemini AI SDK
   - `requests==2.32.5` - HTTP client for Alpha Vantage API
   - `python-dotenv==1.2.1` - Environment variable management

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

### VSCode Configuration
A launch configuration is provided in `.vscode/launch.json`:
- **Python Debugger: Main file** - Runs main.py with integrated terminal

---

## Key Files Reference

### Core Application Files
| File | Lines | Purpose | Dependencies |
|------|-------|---------|--------------|
| `main.py` | 38 | Entry point and workflow orchestration | `ia_analisis`, `news_retriever`, `news` |
| `news_retriever.py` | 77 | Alpha Vantage API integration | `requests`, `python-dotenv`, `news` |
| `ia_analisis.py` | 50 | Gemini AI sentiment analysis | `google.genai`, `python-dotenv` |
| `news.py` | 7 | News data model | None |

### Configuration Files
| File | Purpose |
|------|---------|
| `.env` | API credentials (NEVER commit to git) |
| `.gitignore` | Excludes `.env`, `venv`, `__pycache__`, `.vscode` |
| `requirements.txt` | Python dependencies (62 packages total, mix of project and system packages) |
| `.vscode/launch.json` | VSCode debugger configuration |

### Data Flow
```
User defines ticker + date range
    ↓
Alpha Vantage API returns news feed (JSON)
    ↓
news_retriever.py processes into News objects
    ↓
main.py iterates over News items
    ↓
ia_analisis.py sends each news summary to Gemini AI
    ↓
Gemini returns {SENTIMENT, JUSTIFICATION}
    ↓
Results printed to console
```

---

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints for all function parameters and returns
- Keep functions focused and single-purpose (SRP)
- Prefer explicit over implicit (clear variable names, no magic values)

### Security Best Practices
1. **Never commit API keys** - Always use environment variables
2. **Validate all external inputs** - API responses, user inputs, file contents
3. **Use HTTPS only** - Alpha Vantage and Gemini both support HTTPS
4. **Implement rate limiting** - Protect against API quota exhaustion
5. **Sanitize prompts** - Prevent prompt injection attacks in AI analysis

### Error Handling Strategy
- Use try/except blocks for all external API calls
- Log errors with context (ticker, timestamp, error message)
- Return None or empty collections on failure (fail gracefully)
- Distinguish between recoverable errors (retry) and fatal errors (exit)

### Testing Recommendations
- **Unit Tests**: Test individual functions with mocked API responses
- **Integration Tests**: Test full workflow with real API calls (use test API keys)
- **Edge Cases**: Empty news feeds, malformed JSON, API rate limits, network failures
- **Regression Tests**: Lock in sentiment classifications for known news samples

### Git Workflow
- Current branch: `master`
- Use feature branches for new development
- Write descriptive commit messages
- Review `.gitignore` before committing

---

## Comprehensive Improvement Roadmap

### CRITICAL - Security Issues (Immediate Action Required)

#### 1. API Key Exposure
**Problem**: `.env` file contains actual API keys and is likely committed to git history
**Risk**: High - API keys visible in git history can be scraped by bots
**Solution**:
```bash
# Remove .env from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push to remote (coordinate with team)
git push origin --force --all

# Rotate compromised API keys immediately
# - Get new Gemini API key at https://aistudio.google.com/apikey
# - Get new Alpha Vantage key at https://www.alphavantage.co/support/#api-key
```
**Prevention**: Add `.env` to `.gitignore` (already done), create `.env.example` template

#### 2. Input Validation
**Problem**: No validation of API responses or user inputs
**Risk**: Medium - Malformed data could cause crashes or unexpected behavior
**Solution**:
- Use Pydantic models for all API response validation
- Validate ticker symbols (regex: `^[A-Z]{1,5}$`)
- Validate date ranges (time_from < time_to, not too far in future)
- Validate Gemini response matches expected schema

### HIGH PRIORITY - Functionality Enhancements

#### 3. Data Persistence
**Problem**: Analysis results only printed to console, not saved
**Impact**: Cannot build historical analysis database or backtest strategies
**Solution**:
```python
# Implement SQLite or PostgreSQL storage
class SentimentDatabase:
    def save_analysis(self, ticker, news_item, sentiment, justification, timestamp):
        # Store in database with indexing on ticker, date, sentiment

    def get_historical_sentiment(self, ticker, start_date, end_date):
        # Query sentiment trends over time

    def export_to_csv(self, ticker):
        # Export for external analysis tools
```

#### 4. Batch Processing & Concurrency
**Problem**: Processes news items sequentially, slow for large datasets
**Impact**: Takes 2-3 seconds per news item (API call latency)
**Solution**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def analyze_batch(news_items, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, analyze_news_with_gemini, ticker, item.summary)
            for item in news_items
        ]
        return await asyncio.gather(*tasks)
```

#### 5. CLI Argument Parsing
**Problem**: Ticker and dates hardcoded in main.py
**Impact**: Requires code changes for each run, not user-friendly
**Solution**:
```python
import argparse

parser = argparse.ArgumentParser(description='Analyze market sentiment from news')
parser.add_argument('ticker', help='Stock ticker symbol (e.g., ASTS)')
parser.add_argument('--from', dest='date_from', help='Start date (YYYY-MM-DD)')
parser.add_argument('--to', dest='date_to', help='End date (YYYY-MM-DD)', default='today')
parser.add_argument('--output', help='Output file (JSON/CSV)', default='console')
args = parser.parse_args()
```

#### 6. Rate Limiting & API Cost Management
**Problem**: No protection against API quota exhaustion or cost overruns
**Impact**: Could hit Alpha Vantage rate limits (5 calls/min free tier) or unexpected Gemini costs
**Solution**:
```python
from time import sleep, time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls, period_seconds):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls = deque()

    def wait_if_needed(self):
        now = time()
        # Remove calls outside the time window
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                print(f"Rate limit reached, waiting {sleep_time:.1f}s...")
                sleep(sleep_time)

        self.calls.append(time())

# Usage
alpha_vantage_limiter = RateLimiter(max_calls=5, period_seconds=60)
gemini_limiter = RateLimiter(max_calls=60, period_seconds=60)  # Adjust based on tier
```

#### 7. Caching Strategy
**Problem**: Repeated API calls for same ticker/date waste quota and time
**Impact**: Inefficient during development and backtesting
**Solution**:
```python
import hashlib
import json
from pathlib import Path

class APICache:
    def __init__(self, cache_dir='.cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, ticker, time_from, time_to):
        key_str = f"{ticker}_{time_from}_{time_to}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, ticker, time_from, time_to):
        cache_file = self.cache_dir / f"{self.get_cache_key(ticker, time_from, time_to)}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None

    def set(self, ticker, time_from, time_to, data):
        cache_file = self.cache_dir / f"{self.get_cache_key(ticker, time_from, time_to)}.json"
        cache_file.write_text(json.dumps(data))
```

### MEDIUM PRIORITY - Code Quality

#### 8. Logging Infrastructure
**Problem**: Uses print statements, no structured logging
**Impact**: Hard to debug production issues, no audit trail
**Solution**:
```python
import logging
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"ia_trading_{datetime.now():%Y%m%d}.log"

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )

# Usage
logger = logging.getLogger(__name__)
logger.info(f"Fetching news for {ticker} from {time_from} to {time_to}")
logger.error(f"API error: {e}", exc_info=True)
```

#### 9. Configuration Management
**Problem**: Hardcoded values scattered throughout code (model name, date format, sentiment categories)
**Impact**: Hard to maintain, test, or switch configurations
**Solution**:
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    gemini_api_key: str
    alpha_vantage_api_key: str

    # Model Configuration
    gemini_model: str = "gemini-2.5-flash"
    max_retries: int = 3
    timeout_seconds: int = 30

    # Rate Limiting
    alpha_vantage_calls_per_min: int = 5
    gemini_calls_per_min: int = 60

    # Date Format
    date_format: str = "%Y%m%dT%H%M"

    # Sentiment Categories
    sentiment_categories: list[str] = [
        'Highly Negative', 'Negative', 'Neutral', 'Positive', 'Highly Positive'
    ]

    class Config:
        env_file = '.env'

settings = Settings()
```

#### 10. Use Pydantic for Data Models
**Problem**: Simple News class lacks validation and metadata
**Impact**: Type safety issues, missing data not caught early
**Solution**:
```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class News(BaseModel):
    title: str = Field(..., min_length=1)
    published_date: str  # Could parse to datetime
    summary: str = Field(..., min_length=1)
    source: Optional[str] = None
    url: Optional[str] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    @validator('published_date')
    def validate_date(cls, v):
        # Validate and optionally parse date format
        return v

class SentimentAnalysis(BaseModel):
    ticker: str
    news: News
    sentiment: str = Field(..., regex='^(Highly Negative|Negative|Neutral|Positive|Highly Positive)$')
    justification: str
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    analyzed_at: datetime = Field(default_factory=datetime.now)
```

#### 11. Error Recovery & Retry Logic
**Problem**: API failures cause immediate abort, no retry
**Impact**: Transient network issues cause total failure
**Solution**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError)),
    reraise=True
)
def fetch_raw_data_with_retry(ticker, time_from, time_to):
    return fetch_raw_data(ticker, time_from, time_to)
```

#### 12. Testing Suite
**Problem**: No tests exist
**Impact**: Refactoring is risky, regression bugs likely
**Solution**:
```python
# tests/test_news_retriever.py
import pytest
from unittest.mock import patch, Mock
from news_retriever import process_api_response, build_url

def test_process_api_response_valid_data():
    mock_data = {
        "feed": [
            {"title": "Test", "summary": "Summary", "time_published": "20240101T1200"}
        ]
    }
    result = process_api_response(mock_data)
    assert len(result) == 1
    assert result[0].title == "Test"

def test_process_api_response_empty_feed():
    result = process_api_response({"feed": []})
    assert result == []

def test_build_url_missing_api_key():
    with patch.dict('os.environ', {}, clear=True):
        result = build_url("ASTS", datetime.now(), datetime.now())
        assert result is None

@patch('requests.get')
def test_fetch_raw_data_network_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError()
    result = fetch_raw_data("ASTS", datetime.now(), datetime.now())
    assert result is None
```

### LOWER PRIORITY - Advanced Features

#### 13. Sentiment Aggregation & Scoring
**Problem**: No aggregation of sentiment across multiple news items
**Impact**: Can't get overall market sentiment for a ticker
**Solution**:
```python
class SentimentAggregator:
    sentiment_scores = {
        'Highly Negative': -2,
        'Negative': -1,
        'Neutral': 0,
        'Positive': 1,
        'Highly Positive': 2
    }

    def aggregate(self, analyses: list[SentimentAnalysis]) -> dict:
        if not analyses:
            return {'overall_sentiment': 'Neutral', 'confidence': 0}

        scores = [self.sentiment_scores[a.sentiment] for a in analyses]
        avg_score = sum(scores) / len(scores)

        # Convert back to category
        overall = self._score_to_category(avg_score)

        return {
            'overall_sentiment': overall,
            'average_score': avg_score,
            'news_count': len(analyses),
            'sentiment_distribution': self._get_distribution(analyses)
        }

    def _get_distribution(self, analyses):
        dist = {cat: 0 for cat in self.sentiment_scores.keys()}
        for a in analyses:
            dist[a.sentiment] += 1
        return dist
```

#### 14. Multi-Source News Integration
**Problem**: Only uses Alpha Vantage, limited news coverage
**Impact**: May miss important news from other sources
**Solution**:
```python
# Abstract news source interface
class NewsSource(ABC):
    @abstractmethod
    def fetch_news(self, ticker, time_from, time_to) -> list[News]:
        pass

class AlphaVantageSource(NewsSource):
    def fetch_news(self, ticker, time_from, time_to):
        # Current implementation
        pass

class FinancialModelingPrepSource(NewsSource):
    def fetch_news(self, ticker, time_from, time_to):
        # Fetch from financialmodelingprep.com API
        pass

class NewsAggregator:
    def __init__(self, sources: list[NewsSource]):
        self.sources = sources

    def fetch_all(self, ticker, time_from, time_to):
        all_news = []
        for source in self.sources:
            try:
                news = source.fetch_news(ticker, time_from, time_to)
                all_news.extend(news)
            except Exception as e:
                logger.error(f"Failed to fetch from {source.__class__.__name__}: {e}")

        # Deduplicate by title similarity
        return self._deduplicate(all_news)
```

#### 15. Prompt Engineering Improvements
**Problem**: Single static prompt, no optimization or versioning
**Impact**: Suboptimal sentiment classifications, hard to improve
**Solution**:
```python
# prompts.py
class PromptTemplate:
    def __init__(self, version: str, template: str):
        self.version = version
        self.template = template

    def format(self, **kwargs):
        return self.template.format(**kwargs)

PROMPTS = {
    'v1_basic': PromptTemplate(
        version='v1',
        template="""Act as a quantitative market analyst...{news_text}"""
    ),
    'v2_enhanced': PromptTemplate(
        version='v2',
        template="""You are a senior quantitative analyst at a hedge fund...
        Consider: market impact, price catalysts, sentiment drivers...
        {news_text}"""
    )
}

# A/B test different prompts and track which performs better
def analyze_with_prompt_version(ticker, news_text, prompt_key='v2_enhanced'):
    prompt = PROMPTS[prompt_key].format(ticker=ticker, news_text=news_text)
    # ... rest of analysis
```

#### 16. Backtesting Framework
**Problem**: No way to validate sentiment accuracy against historical price movements
**Impact**: Unknown if sentiment correlates with actual price changes
**Solution**:
```python
import yfinance as yf

class SentimentBacktester:
    def __init__(self, sentiment_db, price_lookforward_days=5):
        self.db = sentiment_db
        self.lookforward = price_lookforward_days

    def backtest(self, ticker, start_date, end_date):
        # Get historical sentiment analyses
        analyses = self.db.get_historical_sentiment(ticker, start_date, end_date)

        # Get price data
        prices = yf.download(ticker, start=start_date, end=end_date)

        results = []
        for analysis in analyses:
            analysis_date = analysis.analyzed_at
            future_date = analysis_date + timedelta(days=self.lookforward)

            price_before = prices.loc[analysis_date]['Close']
            price_after = prices.loc[future_date]['Close']
            price_change = (price_after - price_before) / price_before

            results.append({
                'date': analysis_date,
                'sentiment': analysis.sentiment,
                'price_change': price_change,
                'correct_direction': self._check_direction(analysis.sentiment, price_change)
            })

        return self._calculate_metrics(results)

    def _check_direction(self, sentiment, price_change):
        sentiment_direction = 1 if sentiment in ['Positive', 'Highly Positive'] else -1 if sentiment in ['Negative', 'Highly Negative'] else 0
        price_direction = 1 if price_change > 0 else -1 if price_change < 0 else 0
        return sentiment_direction == price_direction
```

#### 17. Real-Time Monitoring & Alerts
**Problem**: Manual execution only, no continuous monitoring
**Impact**: Miss time-sensitive trading opportunities
**Solution**:
```python
import schedule
import time

class NewsMonitor:
    def __init__(self, tickers: list[str], check_interval_minutes=15):
        self.tickers = tickers
        self.interval = check_interval_minutes
        self.last_check = {}

    def run(self):
        for ticker in self.tickers:
            schedule.every(self.interval).minutes.do(self.check_ticker, ticker)

        while True:
            schedule.run_pending()
            time.sleep(60)

    def check_ticker(self, ticker):
        last_check_time = self.last_check.get(ticker, datetime.now() - timedelta(hours=1))
        news = get_news_data(ticker, last_check_time, datetime.now())

        for news_item in news:
            analysis = analyze_news_with_gemini(ticker, news_item.summary)
            if analysis['SENTIMENT'] in ['Highly Positive', 'Highly Negative']:
                self.send_alert(ticker, news_item, analysis)

        self.last_check[ticker] = datetime.now()

    def send_alert(self, ticker, news_item, analysis):
        # Send email, Slack, Discord, etc.
        print(f"ALERT: {ticker} - {analysis['SENTIMENT']}")
```

#### 18. Web Dashboard
**Problem**: CLI-only interface, not user-friendly for non-technical users
**Impact**: Limited accessibility, no visualization
**Solution**:
```python
# Use Streamlit for rapid dashboard development
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("IA Trading - Market Sentiment Dashboard")

ticker = st.text_input("Enter Ticker Symbol", value="ASTS")
date_range = st.date_input("Select Date Range", value=[...])

if st.button("Analyze"):
    with st.spinner("Fetching news and analyzing sentiment..."):
        news = get_news_data(ticker, date_range[0], date_range[1])
        analyses = analyze_batch(news)

        # Display results
        df = pd.DataFrame([{
            'Date': a.analyzed_at,
            'Title': a.news.title,
            'Sentiment': a.sentiment,
            'Justification': a.justification
        } for a in analyses])

        st.dataframe(df)

        # Sentiment distribution chart
        fig = px.pie(df, names='Sentiment', title='Sentiment Distribution')
        st.plotly_chart(fig)
```

#### 19. Export & Reporting
**Problem**: No structured output formats for downstream analysis
**Impact**: Hard to integrate with other tools
**Solution**:
```python
class ReportExporter:
    def export_json(self, analyses, filename):
        with open(filename, 'w') as f:
            json.dump([a.dict() for a in analyses], f, indent=2, default=str)

    def export_csv(self, analyses, filename):
        df = pd.DataFrame([{
            'ticker': a.ticker,
            'date': a.analyzed_at,
            'title': a.news.title,
            'sentiment': a.sentiment,
            'justification': a.justification,
            'confidence': a.confidence_score
        } for a in analyses])
        df.to_csv(filename, index=False)

    def export_html_report(self, analyses, filename):
        # Generate HTML report with charts and tables
        pass
```

#### 20. Docker Containerization
**Problem**: Manual setup required, environment inconsistencies
**Impact**: Deployment complexity, hard to scale
**Solution**:
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  ia-trading:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

---

## Requirements.txt Issues

The current `requirements.txt` contains 62 packages, many of which are system-level Ubuntu packages unrelated to the project. This is problematic because:

1. Includes system packages like `cloud-init`, `ubuntu-pro-client`, `python-apt`
2. Mixes application dependencies with OS dependencies
3. Makes clean installation on other systems impossible
4. Version conflicts likely on different OS versions

**Correct requirements.txt should be**:
```
google-genai==1.52.0
requests==2.32.5
python-dotenv==1.2.1

# Optional enhancements
pydantic==2.12.5
tenacity==9.1.2
pytest==8.0.0  # for testing
```

Generate correctly with:
```bash
pip freeze | grep -E "google-genai|requests|python-dotenv" > requirements.txt
```

---

## Performance Considerations

### Current Performance Profile
- **News Retrieval**: ~1-2 seconds per API call (network latency)
- **AI Analysis**: ~2-3 seconds per news item (Gemini API latency)
- **Total Time**: For 10 news items: ~30-50 seconds (sequential processing)

### Optimization Strategies

1. **Parallel Processing**: Use ThreadPoolExecutor for concurrent API calls (5-10x speedup)
2. **Batch Gemini Requests**: Analyze multiple news items in single prompt (reduce API calls)
3. **Caching**: Cache API responses to avoid redundant calls
4. **Local Sentiment Model**: Consider running local lightweight sentiment model for screening, use Gemini for final analysis

### Cost Considerations

**Alpha Vantage Free Tier**:
- 5 API calls per minute
- 25 calls per day
- Cost: Free

**Google Gemini Pricing** (as of 2024):
- gemini-2.5-flash: ~$0.0001 per 1K tokens (input), ~$0.0003 per 1K tokens (output)
- Average news analysis: ~500 input tokens, ~100 output tokens
- Cost per analysis: ~$0.00008
- 1000 analyses: ~$0.08 (very affordable)

---

## Common Issues & Troubleshooting

### Issue: "FATAL ERROR: Could not initialize the Gemini client"
**Cause**: Missing or invalid GEMINI_API_KEY in .env
**Solution**:
1. Verify `.env` file exists in project root
2. Check API key is valid at https://aistudio.google.com/apikey
3. Ensure no spaces around the `=` in `.env`

### Issue: "ERROR: ALPHA_VANTAGE_API_KEY not found in .env"
**Cause**: Missing Alpha Vantage API key
**Solution**: Sign up at https://www.alphavantage.co and add key to `.env`

### Issue: No news items found
**Causes**:
1. Invalid ticker symbol
2. No news in specified date range
3. API rate limit exceeded
**Solution**:
- Verify ticker on finance.yahoo.com
- Expand date range
- Check Alpha Vantage API status

### Issue: AI returns invalid JSON
**Cause**: Gemini API sometimes returns malformed responses
**Solution**: Add retry logic with exponential backoff (see improvement #11)

---

## Future Roadmap Priorities

### Phase 1: Production Readiness (2-3 weeks)
1. Fix security issues (API key rotation, .env exclusion from git)
2. Add comprehensive error handling and retry logic
3. Implement logging infrastructure
4. Create test suite (>80% coverage)
5. Use Pydantic for data validation
6. Clean up requirements.txt

### Phase 2: Core Features (3-4 weeks)
1. Add CLI argument parsing
2. Implement data persistence (SQLite)
3. Add caching layer
4. Implement rate limiting
5. Batch processing with concurrency
6. Create configuration management system

### Phase 3: Advanced Analytics (4-6 weeks)
1. Sentiment aggregation and scoring
2. Backtesting framework
3. Multi-source news integration
4. Export to CSV/JSON/HTML
5. Historical trend analysis

### Phase 4: Production Deployment (3-4 weeks)
1. Docker containerization
2. Real-time monitoring system
3. Alert system (email/Slack/Discord)
4. Web dashboard (Streamlit)
5. API endpoints (FastAPI)
6. Horizontal scaling support

---

## Additional Resources

### Alpha Vantage API Documentation
- Main Docs: https://www.alphavantage.co/documentation/
- News Sentiment API: https://www.alphavantage.co/documentation/#news-sentiment

### Google Gemini Documentation
- Getting Started: https://ai.google.dev/gemini-api/docs
- Python SDK: https://github.com/googleapis/python-genai
- Pricing: https://ai.google.dev/pricing

### Trading System Best Practices
- "Algorithmic Trading" by Ernest P. Chan
- QuantConnect Learn: https://www.quantconnect.com/learning
- Backtesting best practices: https://www.quantstart.com/articles/

---

## Contact & Contribution

This is a personal project for educational and research purposes.

**Development Notes**:
- Currently at prototype stage (~172 lines of code)
- Not production-ready for live trading
- Use at your own risk for real financial decisions
- No warranty or guarantee of accuracy

**Next Developer Notes**:
- Read this entire document before making changes
- Follow the improvement roadmap priorities
- Add tests for all new features
- Update this document when adding major features
- Never commit API keys or sensitive data

---

*Last Updated: 2025-12-23*
*Documentation Version: 1.0*
