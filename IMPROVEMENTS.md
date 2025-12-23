# IA Trading - Prioritized Improvements List

## Executive Summary

The ia-trading project is a functional prototype for market sentiment analysis using AI. However, it requires significant improvements across security, reliability, functionality, and code quality to be production-ready.

**Current State**: 172 lines of code, basic functionality working
**Recommended Timeline**: 12-16 weeks to production-ready
**Critical Security Issue**: API keys exposed in git history - requires immediate action

---

## CRITICAL ISSUES (Fix Immediately)

### 1. API Key Security Breach
**Severity**: CRITICAL
**Effort**: 30 minutes
**Risk**: API keys visible in git history, potential unauthorized usage

**Action Required**:
```bash
# 1. Remove .env from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 2. Rotate all API keys immediately
# - Get new Gemini API key: https://aistudio.google.com/apikey
# - Get new Alpha Vantage key: https://www.alphavantage.co/support/#api-key

# 3. Create .env.example template
echo "GEMINI_API_KEY=your_gemini_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here" > .env.example

# 4. Verify .env is in .gitignore
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

# 5. Force push to remote (WARNING: coordinate with team)
git push origin --force --all
```

**Prevention**: Never commit `.env` files, always use `.env.example` as template

---

## HIGH PRIORITY (Weeks 1-2)

### 2. Fix requirements.txt
**Severity**: High
**Effort**: 10 minutes
**Problem**: Contains 62 packages including Ubuntu system packages

**Action**:
```bash
# Create clean requirements.txt
cat > requirements.txt << 'EOF'
google-genai==1.52.0
requests==2.32.5
python-dotenv==1.2.1
pydantic==2.12.5
tenacity==9.1.2

# Testing
pytest==8.0.0
pytest-cov==4.1.0
pytest-mock==3.12.0
EOF
```

**Files to modify**: `requirements.txt`

### 3. Add Comprehensive Error Handling
**Severity**: High
**Effort**: 4 hours
**Problem**: Minimal error handling, crashes on API failures

**Implementation**:

```python
# news_retriever.py - Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def fetch_raw_data_with_retry(ticker, time_from, time_to):
    """Fetch with automatic retries on failure"""
    return fetch_raw_data(ticker, time_from, time_to)

# ia_analisis.py - Handle initialization gracefully
def initialize_gemini_client():
    """Initialize client with proper error handling"""
    try:
        return genai.Client()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None

client = initialize_gemini_client()

def analyze_news_with_gemini(ticker, news_text):
    if client is None:
        logger.error("Gemini client not initialized, skipping analysis")
        return None
    # ... rest of implementation
```

**Files to modify**: `news_retriever.py`, `ia_analisis.py`

### 4. Implement Structured Logging
**Severity**: High
**Effort**: 2 hours
**Problem**: Uses print statements, no audit trail

**Implementation**:

```python
# logging_config.py (new file)
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """Configure application logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"ia_trading_{datetime.now():%Y%m%d}.log"

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s - %(message)s')

    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler - simple logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler]
    )

# main.py - Use logging
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting analysis for ticker: {ticker}")
    logger.info(f"Date range: {time_from} to {time_to}")
    # ... rest of code
```

**Files to create**: `logging_config.py`
**Files to modify**: `main.py`, `news_retriever.py`, `ia_analisis.py`

### 5. Add Input Validation with Pydantic
**Severity**: High
**Effort**: 3 hours
**Problem**: No validation of inputs or API responses

**Implementation**:

```python
# models.py (new file)
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class News(BaseModel):
    """Validated News data model"""
    title: str = Field(..., min_length=1, max_length=500)
    published_date: str = Field(..., regex=r'^\d{8}T\d{4}$')
    summary: str = Field(..., min_length=10)
    source: Optional[str] = None
    url: Optional[str] = None

    @validator('title', 'summary')
    def clean_text(cls, v):
        """Strip whitespace and validate"""
        return v.strip()

class SentimentAnalysis(BaseModel):
    """Validated sentiment analysis result"""
    ticker: str = Field(..., regex=r'^[A-Z]{1,5}$')
    news: News
    sentiment: str = Field(
        ...,
        regex=r'^(Highly Negative|Negative|Neutral|Positive|Highly Positive)$'
    )
    justification: str = Field(..., min_length=10, max_length=500)
    analyzed_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

class AlphaVantageResponse(BaseModel):
    """Validate Alpha Vantage API response"""
    feed: list[dict]
    items: Optional[str] = None
    sentiment_score_definition: Optional[str] = None

    @validator('feed')
    def validate_feed(cls, v):
        if not isinstance(v, list):
            raise ValueError("Feed must be a list")
        return v
```

**Files to create**: `models.py`
**Files to modify**: `news.py` (replace with import from models), `news_retriever.py`, `ia_analisis.py`

---

## MEDIUM PRIORITY (Weeks 3-4)

### 6. Add CLI Argument Parsing
**Severity**: Medium
**Effort**: 2 hours
**Problem**: Hardcoded ticker and dates, requires code changes for each run

**Implementation**:

```python
# cli.py (new file)
import argparse
from datetime import datetime, timedelta

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Analyze market sentiment from news using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ASTS --from 2024-01-01 --to 2024-12-31
  python main.py TSLA --days 30 --output results.json
  python main.py AAPL --from 2024-11-01  # defaults to today
        """
    )

    parser.add_argument(
        'ticker',
        type=str,
        help='Stock ticker symbol (e.g., ASTS, TSLA, AAPL)'
    )

    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        '--from',
        dest='date_from',
        type=str,
        help='Start date (YYYY-MM-DD format)'
    )
    date_group.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days back from today (default: 30)'
    )

    parser.add_argument(
        '--to',
        dest='date_to',
        type=str,
        help='End date (YYYY-MM-DD format, default: today)'
    )

    parser.add_argument(
        '--output',
        type=str,
        choices=['console', 'json', 'csv'],
        default='console',
        help='Output format (default: console)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Validate and convert dates
    if args.date_from:
        args.time_from = datetime.strptime(args.date_from, '%Y-%m-%d')
    else:
        args.time_from = datetime.now() - timedelta(days=args.days)

    if args.date_to:
        args.time_to = datetime.strptime(args.date_to, '%Y-%m-%d')
    else:
        args.time_to = datetime.now()

    # Validate ticker format
    args.ticker = args.ticker.upper()
    if not args.ticker.isalpha() or len(args.ticker) > 5:
        parser.error(f"Invalid ticker symbol: {args.ticker}")

    # Validate date range
    if args.time_from >= args.time_to:
        parser.error("Start date must be before end date")

    return args

# main.py - Use CLI
from cli import parse_arguments

if __name__ == "__main__":
    args = parse_arguments()

    ticker = args.ticker
    time_from = args.time_from
    time_to = args.time_to

    logger.info(f"Analyzing {ticker} from {time_from:%Y-%m-%d} to {time_to:%Y-%m-%d}")
    # ... rest of code
```

**Files to create**: `cli.py`
**Files to modify**: `main.py`

### 7. Implement Data Persistence
**Severity**: Medium
**Effort**: 6 hours
**Problem**: No storage of analysis results, everything lost on exit

**Implementation**:

```python
# database.py (new file)
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json
from models import SentimentAnalysis, News

class SentimentDatabase:
    """SQLite database for sentiment analysis storage"""

    def __init__(self, db_path='data/sentiment.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None
        self.initialize_schema()

    def initialize_schema(self):
        """Create database tables"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    published_date TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sentiment_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    justification TEXT NOT NULL,
                    analyzed_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (news_id) REFERENCES news(id)
                );

                CREATE INDEX IF NOT EXISTS idx_ticker_date
                ON sentiment_analysis(ticker, analyzed_at);

                CREATE INDEX IF NOT EXISTS idx_sentiment
                ON sentiment_analysis(sentiment);
            """)

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def save_analysis(self, analysis: SentimentAnalysis) -> int:
        """Save sentiment analysis to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert news
            cursor.execute("""
                INSERT INTO news (title, published_date, summary, source, url)
                VALUES (?, ?, ?, ?, ?)
            """, (
                analysis.news.title,
                analysis.news.published_date,
                analysis.news.summary,
                analysis.news.source,
                analysis.news.url
            ))
            news_id = cursor.lastrowid

            # Insert analysis
            cursor.execute("""
                INSERT INTO sentiment_analysis
                (news_id, ticker, sentiment, justification, analyzed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                news_id,
                analysis.ticker,
                analysis.sentiment,
                analysis.justification,
                analysis.analyzed_at
            ))

            conn.commit()
            return cursor.lastrowid

    def get_analyses(
        self,
        ticker: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sentiment: Optional[str] = None
    ) -> List[dict]:
        """Query sentiment analyses with filters"""
        query = """
            SELECT
                sa.id,
                sa.ticker,
                sa.sentiment,
                sa.justification,
                sa.analyzed_at,
                n.title,
                n.published_date,
                n.summary
            FROM sentiment_analysis sa
            JOIN news n ON sa.news_id = n.id
            WHERE 1=1
        """
        params = []

        if ticker:
            query += " AND sa.ticker = ?"
            params.append(ticker)

        if start_date:
            query += " AND sa.analyzed_at >= ?"
            params.append(start_date)

        if end_date:
            query += " AND sa.analyzed_at <= ?"
            params.append(end_date)

        if sentiment:
            query += " AND sa.sentiment = ?"
            params.append(sentiment)

        query += " ORDER BY sa.analyzed_at DESC"

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def export_to_json(self, ticker: str, filename: str):
        """Export analyses to JSON file"""
        analyses = self.get_analyses(ticker=ticker)
        with open(filename, 'w') as f:
            json.dump(analyses, f, indent=2, default=str)

    def export_to_csv(self, ticker: str, filename: str):
        """Export analyses to CSV file"""
        import csv
        analyses = self.get_analyses(ticker=ticker)

        if not analyses:
            return

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=analyses[0].keys())
            writer.writeheader()
            writer.writerows(analyses)

# main.py - Use database
from database import SentimentDatabase
from models import SentimentAnalysis

db = SentimentDatabase()

for i, news_item in enumerate(news_list):
    analysis_result = analyze_news_with_gemini(ticker, news_item.summary)

    if analysis_result:
        # Create validated analysis object
        analysis = SentimentAnalysis(
            ticker=ticker,
            news=news_item,
            sentiment=analysis_result['SENTIMENT'],
            justification=analysis_result['JUSTIFICATION']
        )

        # Save to database
        analysis_id = db.save_analysis(analysis)
        logger.info(f"Saved analysis {analysis_id} to database")

        # Print to console
        print(f"SENTIMENT: {analysis.sentiment}")
        print(f"JUSTIFICATION: {analysis.justification}")
```

**Files to create**: `database.py`, `data/` directory
**Files to modify**: `main.py`

### 8. Add Rate Limiting
**Severity**: Medium
**Effort**: 2 hours
**Problem**: No protection against API quota exhaustion

**Implementation**:

```python
# rate_limiter.py (new file)
from time import sleep, time
from collections import deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_calls: int, period_seconds: int):
        """
        Args:
            max_calls: Maximum number of calls allowed in the time period
            period_seconds: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls = deque()

    def wait_if_needed(self):
        """Block if rate limit would be exceeded"""
        now = time()

        # Remove calls outside the time window
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached ({self.max_calls} calls per {self.period}s), "
                    f"waiting {sleep_time:.1f}s..."
                )
                sleep(sleep_time)

        self.calls.append(time())

# news_retriever.py - Use rate limiter
from rate_limiter import RateLimiter

# Alpha Vantage free tier: 5 calls/min
alpha_vantage_limiter = RateLimiter(max_calls=5, period_seconds=60)

def fetch_raw_data(ticker, time_from, time_to):
    alpha_vantage_limiter.wait_if_needed()
    # ... rest of implementation

# ia_analisis.py - Use rate limiter for Gemini
from rate_limiter import RateLimiter

# Adjust based on your Gemini tier
gemini_limiter = RateLimiter(max_calls=60, period_seconds=60)

def analyze_news_with_gemini(ticker, news_text):
    gemini_limiter.wait_if_needed()
    # ... rest of implementation
```

**Files to create**: `rate_limiter.py`
**Files to modify**: `news_retriever.py`, `ia_analisis.py`

### 9. Add Caching
**Severity**: Medium
**Effort**: 3 hours
**Problem**: Repeated API calls waste quota and time

**Implementation**:

```python
# cache.py (new file)
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class APICache:
    """File-based cache for API responses"""

    def __init__(self, cache_dir='.cache', ttl_hours=24):
        """
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (0 = never expire)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours) if ttl_hours > 0 else None

    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        key_str = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{key}.json"

    def get(self, *args):
        """Get cached data if exists and not expired"""
        key = self._get_cache_key(*args)
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return None

        # Check TTL
        if self.ttl:
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_age > self.ttl:
                logger.debug(f"Cache expired for key {key}")
                cache_file.unlink()
                return None

        logger.debug(f"Cache hit for key {key}")
        return json.loads(cache_file.read_text())

    def set(self, data, *args):
        """Save data to cache"""
        key = self._get_cache_key(*args)
        cache_file = self._get_cache_file(key)
        cache_file.write_text(json.dumps(data, default=str))
        logger.debug(f"Cached data with key {key}")

    def clear(self):
        """Clear all cache files"""
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()
        logger.info("Cache cleared")

# news_retriever.py - Use cache
from cache import APICache

news_cache = APICache(cache_dir='.cache/news', ttl_hours=24)

def fetch_raw_data(ticker, time_from, time_to):
    # Check cache first
    cached_data = news_cache.get(ticker, time_from, time_to)
    if cached_data:
        logger.info(f"Using cached news data for {ticker}")
        return cached_data

    # Fetch from API
    url = build_url(ticker, time_from, time_to)
    # ... fetch logic ...

    # Cache the response
    news_cache.set(data, ticker, time_from, time_to)
    return data
```

**Files to create**: `cache.py`, `.cache/` directory
**Files to modify**: `news_retriever.py`

---

## LOWER PRIORITY (Weeks 5-8)

### 10. Add Unit Tests
**Severity**: Low
**Effort**: 8 hours
**Problem**: No tests, risky to refactor

**Implementation**:

```python
# tests/test_news_retriever.py
import pytest
from unittest.mock import patch, Mock
from datetime import datetime
from news_retriever import process_api_response, build_url, fetch_raw_data
from models import News

@pytest.fixture
def sample_api_response():
    return {
        "feed": [
            {
                "title": "Test News",
                "summary": "This is a test summary",
                "time_published": "20240101T1200"
            }
        ]
    }

def test_process_api_response_valid_data(sample_api_response):
    result = process_api_response(sample_api_response)
    assert len(result) == 1
    assert isinstance(result[0], News)
    assert result[0].title == "Test News"

def test_process_api_response_empty_feed():
    result = process_api_response({"feed": []})
    assert result == []

def test_process_api_response_missing_feed():
    result = process_api_response({})
    assert result == []

@patch.dict('os.environ', {'ALPHA_VANTAGE_API_KEY': 'test_key'})
def test_build_url_valid():
    time_from = datetime(2024, 1, 1)
    time_to = datetime(2024, 1, 31)
    url = build_url("ASTS", time_from, time_to)

    assert url is not None
    assert "ASTS" in url
    assert "test_key" in url
    assert "20240101T0000" in url

@patch.dict('os.environ', {}, clear=True)
def test_build_url_missing_api_key():
    result = build_url("ASTS", datetime.now(), datetime.now())
    assert result is None

@patch('requests.get')
def test_fetch_raw_data_success(mock_get, sample_api_response):
    mock_get.return_value.json.return_value = sample_api_response
    mock_get.return_value.raise_for_status = Mock()

    result = fetch_raw_data("ASTS", datetime.now(), datetime.now())
    assert result == sample_api_response

@patch('requests.get')
def test_fetch_raw_data_network_error(mock_get):
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError()

    result = fetch_raw_data("ASTS", datetime.now(), datetime.now())
    assert result is None

# tests/test_ia_analisis.py
import pytest
from unittest.mock import Mock, patch
from ia_analisis import analyze_news_with_gemini

@patch('ia_analisis.client')
def test_analyze_news_valid_response(mock_client):
    mock_response = Mock()
    mock_response.text = '{"SENTIMENT": "Positive", "JUSTIFICATION": "Good news"}'
    mock_client.models.generate_content.return_value = mock_response

    result = analyze_news_with_gemini("ASTS", "Test news")

    assert result is not None
    assert result['SENTIMENT'] == 'Positive'
    assert result['JUSTIFICATION'] == 'Good news'

@patch('ia_analisis.client')
def test_analyze_news_invalid_json(mock_client):
    mock_response = Mock()
    mock_response.text = 'invalid json'
    mock_client.models.generate_content.return_value = mock_response

    result = analyze_news_with_gemini("ASTS", "Test news")
    assert result is None

# Run tests with coverage
# pytest --cov=. --cov-report=html --cov-report=term
```

**Files to create**: `tests/test_news_retriever.py`, `tests/test_ia_analisis.py`, `tests/conftest.py`
**New dependency**: `pytest`, `pytest-cov`, `pytest-mock`

### 11. Add Configuration Management
**Severity**: Low
**Effort**: 2 hours

**Implementation**:

```python
# config.py (new file)
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application configuration"""

    # API Keys
    gemini_api_key: str
    alpha_vantage_api_key: str

    # Model Configuration
    gemini_model: str = "gemini-2.5-flash"
    max_retries: int = 3
    timeout_seconds: int = 30

    # Rate Limiting
    alpha_vantage_calls_per_min: int = 5
    gemini_calls_per_min: int = 60

    # Caching
    cache_enabled: bool = True
    cache_ttl_hours: int = 24

    # Database
    database_path: str = "data/sentiment.db"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"

    # Date Format
    date_format: str = "%Y%m%dT%H%M"

    # Sentiment Categories
    sentiment_categories: List[str] = [
        'Highly Negative', 'Negative', 'Neutral', 'Positive', 'Highly Positive'
    ]

    class Config:
        env_file = '.env'
        case_sensitive = False

# Singleton instance
settings = Settings()
```

**Files to create**: `config.py`
**Files to modify**: All files to use `settings` instead of hardcoded values

### 12-20. Additional Features
See CLAUDE.md for detailed implementations of:
- Sentiment aggregation
- Backtesting framework
- Multi-source integration
- Real-time monitoring
- Web dashboard
- Export/reporting
- Docker containerization

---

## Quick Start Improvement Path

If you have limited time, focus on these improvements in order:

1. **Security** (30 min): Rotate API keys, clean git history
2. **Requirements** (10 min): Fix requirements.txt
3. **Logging** (2 hours): Replace print with logging
4. **Error Handling** (4 hours): Add retry logic and validation
5. **CLI** (2 hours): Add argument parsing
6. **Tests** (4 hours): Add basic test coverage

Total: ~12 hours to significantly improve code quality

---

## Testing Checklist

Before deploying any changes:

- [ ] Rotate API keys if .env was in git
- [ ] Test with invalid ticker symbols
- [ ] Test with empty date ranges (no news)
- [ ] Test with API rate limit exceeded
- [ ] Test with network disconnected
- [ ] Test with invalid API keys
- [ ] Test with malformed API responses
- [ ] Run pytest with >80% coverage
- [ ] Test CLI with various argument combinations
- [ ] Verify logs are being written
- [ ] Check database persistence works
- [ ] Verify cache works and expires correctly

---

*Generated: 2025-12-23*
*Priority Level: CRITICAL items must be addressed before production use*
