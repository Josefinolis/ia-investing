# IA Trading - Market Sentiment Analysis Tool

## Project Overview

**IA Trading** is a production-ready Python CLI tool that analyzes news sentiment for publicly traded companies using AI. It retrieves financial news from **multiple sources** (Alpha Vantage, Reddit, Twitter) and uses Google's Gemini AI to classify sentiment, providing trading signals and actionable insights.

### Key Features
- **Multi-source news aggregation** (Alpha Vantage, Reddit, Twitter)
- Sentiment analysis with 5 categories (Highly Negative to Highly Positive)
- Trading signals (STRONG BUY, BUY, HOLD, SELL, STRONG SELL)
- Time-weighted scoring with trend detection
- Batch processing for multiple tickers
- SQLite database persistence
- Export to JSON, CSV, and HTML reports
- API response caching
- Rate limiting and retry logic

---

## Quick Start

### Installation
```bash
cd /home/os_uis/projects/ia_trading
pip install -r requirements.txt
```

### Configuration
Create a `.env` file (use `.env.example` as template):
```bash
# Required
ALPHA_VANTAGE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Optional - Reddit API (for social sentiment)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Optional - Twitter (disabled by default, Nitter instances unreliable)
TWITTER_ENABLED=false
```

### Usage Examples
```bash
# Basic analysis (last 7 days)
python main.py AAPL

# Custom date range
python main.py TSLA --days 30
python main.py MSFT --from 2024-01-01 --to 2024-12-31

# With trading signal
python main.py NVDA --score

# Batch analysis
python main.py AAPL,MSFT,GOOGL,AMZN --score

# Export results
python main.py TSLA --export json
python main.py NVDA --export html

# Save to database
python main.py AAPL --save

# View historical summary
python main.py AAPL --summary

# Fresh data (skip cache)
python main.py TSLA --no-cache
```

### Production API

The API is deployed on a VPS (IONOS Debian 12) with automatic deployment via GitHub Actions.

**Production URL:** http://195.20.235.94

**Deployment:** Push to `master` triggers automatic build and deploy.

**Infrastructure docs:** https://github.com/Josefinolis/documentation

### Running Locally (Development)

```bash
# Activate virtual environment
cd /home/os_uis/projects/ia_trading
source venv/bin/activate

# Start the API server (development)
uvicorn api.main:app --host 0.0.0.0 --port 8000

# With auto-reload for development
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**API Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GET /` | API info |
| `GET /health` | Health check |
| `GET /docs` | Swagger UI documentation |
| `GET /api/tickers` | List all tracked tickers |
| `POST /api/tickers` | Add a new ticker (does NOT fetch news) |
| `GET /api/tickers/{symbol}` | Get ticker details with news |
| `DELETE /api/tickers/{symbol}` | Remove a ticker |
| `POST /api/tickers/{symbol}/fetch` | Trigger news fetch for ticker |
| `POST /api/tickers/{symbol}/analyze` | Trigger analysis for ticker |
| `GET /api/jobs/status` | Job tracker status |
| `POST /api/jobs/fetch` | Trigger news fetch for all tickers |
| `POST /api/jobs/analyze` | Trigger analysis for all pending |

**For Android Emulator:** Use `http://10.0.2.2:8000` (maps to host's localhost:8000).
**For Physical Device:** Use `http://195.20.235.94` (production VPS).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│  CLI entry point, argument parsing, display, orchestration       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        v                     v                     v
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│news_retriever │    │  ia_analisis  │    │   database    │
│               │    │               │    │               │
│  Aggregator   │    │  Gemini AI    │    │   SQLite      │
│  Multi-source │    │  Analysis     │    │   Storage     │
└───────────────┘    └───────────────┘    └───────────────┘
        │
        v
┌─────────────────────────────────────────────────────┐
│                   news_sources/                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │Alpha Vantage│ │   Reddit    │ │   Twitter   │   │
│  │  (API)      │ │   (PRAW)    │ │ (ntscraper) │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## News Sources

The system supports multiple news sources that are aggregated and deduplicated:

| Source | Type | Configuration | Status |
|--------|------|---------------|--------|
| **Alpha Vantage** | Financial News API | `ALPHA_VANTAGE_API_KEY` | Required |
| **Reddit** | Social Media (PRAW) | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | Optional |
| **Twitter** | Social Media (ntscraper) | `TWITTER_ENABLED` | Optional (disabled by default) |

### Configuring Reddit

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Fill in:
   - **name**: `ia_trading`
   - **type**: `script`
   - **redirect uri**: `http://localhost:8080`
4. Click "create app"
5. Copy the client ID (under app name) and secret
6. Add to `.env`:
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
```

**Default subreddits searched:** `wallstreetbets`, `stocks`, `investing`, `stockmarket`, `options`

### Configuring Twitter

Twitter uses ntscraper (Nitter-based scraping). No API key required, but Nitter instances are often unreliable.

```bash
# Enable Twitter (disabled by default)
TWITTER_ENABLED=true

# Optional settings
TWITTER_MIN_LIKES=10
TWITTER_MIN_RETWEETS=5
TWITTER_MAX_RESULTS=50
```

> **Note:** Twitter scraping may not work reliably as public Nitter instances are frequently blocked by Twitter/X.

---

## Module Reference

### Core Modules

| Module | Purpose |
|--------|---------|
| `main.py` | CLI entry point, argument parsing, display |
| `news_retriever.py` | Multi-source news aggregation |
| `ia_analisis.py` | Gemini AI sentiment analysis |
| `database.py` | SQLite persistence |
| `models.py` | Pydantic data models |
| `config.py` | Configuration management |

### News Sources Package

| Module | Purpose |
|--------|---------|
| `news_sources/base.py` | Abstract base class for news sources |
| `news_sources/alpha_vantage.py` | Alpha Vantage API integration |
| `news_sources/reddit.py` | Reddit API via PRAW |
| `news_sources/twitter.py` | Twitter via ntscraper |
| `news_sources/aggregator.py` | Combines and deduplicates all sources |

### Feature Modules

| Module | Purpose |
|--------|---------|
| `cache.py` | File-based API response caching |
| `exporter.py` | JSON, CSV, HTML export |
| `scoring.py` | Sentiment aggregation and trading signals |
| `logger.py` | Structured logging with Rich |
| `rate_limit_manager.py` | Centralized rate limiting |

### Test Modules

| Module | Purpose |
|--------|---------|
| `tests/test_models.py` | Model validation tests |
| `tests/test_config.py` | Configuration tests |
| `tests/test_news_retriever.py` | API integration tests |

---

## Data Models

### NewsItem
```python
class NewsItem(BaseModel):
    title: str
    summary: str
    published_date: str
    source: Optional[str]           # e.g., "Reuters", "r/wallstreetbets"
    source_type: Optional[str]      # "alpha_vantage", "reddit", "twitter"
    url: Optional[str]
    relevance_score: Optional[float]
    engagement_score: Optional[int] # Social engagement (likes, upvotes)
    author: Optional[str]
    author_followers: Optional[int]
```

### SentimentCategory
```python
class SentimentCategory(str, Enum):
    HIGHLY_NEGATIVE = "Highly Negative"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"
    POSITIVE = "Positive"
    HIGHLY_POSITIVE = "Highly Positive"
```

### Trading Signals
| Score Range | Signal |
|-------------|--------|
| >= 0.5 | STRONG BUY |
| >= 0.2 | BUY |
| >= -0.2 | HOLD |
| >= -0.5 | SELL |
| < -0.5 | STRONG SELL |

---

## CLI Options

| Option | Description |
|--------|-------------|
| `ticker` | Stock symbol(s), comma-separated for batch |
| `--days N` | Look back N days (default: 7) |
| `--from DATE` | Start date (YYYY-MM-DD) |
| `--to DATE` | End date (YYYY-MM-DD) |
| `--save` | Save to SQLite database |
| `--summary` | Show historical summary from database |
| `--export FORMAT` | Export to json, csv, or html |
| `--score` | Show sentiment score and trading signal |
| `--batch` | Enable batch processing mode |
| `--limit N` | Max news items to analyze (default: 50) |
| `--no-cache` | Disable caching, fetch fresh data |
| `--no-analyze` | Fetch news only, skip AI analysis |
| `-v, --verbose` | Enable verbose output |

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `REDDIT_CLIENT_ID` | Reddit app client ID | No |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret | No |
| `REDDIT_SUBREDDITS` | Comma-separated subreddits | No |
| `REDDIT_MIN_SCORE` | Minimum post score (default: 10) | No |
| `TWITTER_ENABLED` | Enable Twitter source (default: false) | No |
| `TWITTER_MIN_LIKES` | Minimum likes (default: 10) | No |
| `TWITTER_MIN_RETWEETS` | Minimum retweets (default: 5) | No |

### Settings (config.py)
| Setting | Default | Description |
|---------|---------|-------------|
| `gemini_model` | gemini-2.5-flash-lite | AI model to use |
| `max_retries` | 3 | API retry attempts |
| `database_url` | sqlite:///ia_trading.db | Database location |
| `alpha_vantage_calls_per_minute` | 5 | Rate limit |
| `gemini_calls_per_minute` | 15 | Rate limit |

---

## Development

### Running Tests
```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

### Code Style
```bash
black .
isort .
mypy .
```

### Project Structure
```
ia_trading/
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── models.py            # Pydantic data models
├── news_retriever.py    # Multi-source news aggregation
├── ia_analisis.py       # Gemini AI analysis
├── database.py          # SQLite persistence
├── cache.py             # API caching
├── exporter.py          # Export functionality
├── scoring.py           # Sentiment scoring
├── logger.py            # Logging configuration
├── rate_limit_manager.py # Rate limiting
├── news_sources/        # News source implementations
│   ├── __init__.py
│   ├── base.py          # Abstract base class
│   ├── alpha_vantage.py # Alpha Vantage API
│   ├── reddit.py        # Reddit via PRAW
│   ├── twitter.py       # Twitter via ntscraper
│   └── aggregator.py    # Source aggregator
├── api/                 # FastAPI REST API
│   ├── main.py
│   ├── schemas.py
│   └── routers/
├── services/            # Business logic services
├── schedulers/          # Background job schedulers
├── requirements.txt     # Dependencies
├── .env                 # API keys (not in git)
├── .env.example         # Template for .env
├── .gitignore           # Git exclusions
├── CLAUDE.md            # This file
└── tests/
    ├── test_models.py
    ├── test_config.py
    └── test_news_retriever.py
```

---

## API Rate Limits

| Service | Free Tier Limit |
|---------|-----------------|
| Alpha Vantage | 5 calls/minute, 500 calls/day |
| Gemini | 15 RPM, 1M tokens/minute |
| Reddit | 60 requests/minute |
| Twitter | N/A (scraping) |

The tool handles rate limiting automatically with `ratelimit` and `tenacity` libraries.

---

## Troubleshooting

### No news items found
- Check if the ticker symbol is valid
- Try a longer date range with `--days 30`
- Verify Alpha Vantage API key is valid

### API rate limit exceeded
- Wait 60 seconds between runs
- Use `--limit` to reduce requests
- Results are cached by default

### Configuration error
- Ensure `.env` file exists with valid keys
- Check `.env.example` for required variables

### Reddit not working
- Verify credentials at https://www.reddit.com/prefs/apps
- Ensure app type is "script"
- Check if account email is verified
- New accounts may need to wait a few days

### Twitter not working
- Twitter/ntscraper relies on public Nitter instances
- These are frequently blocked by Twitter/X
- Consider disabling with `TWITTER_ENABLED=false`
