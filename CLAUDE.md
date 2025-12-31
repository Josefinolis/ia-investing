# IA Trading - Market Sentiment Analysis Tool

## Project Overview

**IA Trading** is a production-ready Python CLI tool that analyzes news sentiment for publicly traded companies using AI. It retrieves financial news via Alpha Vantage API and uses Google's Gemini AI to classify sentiment, providing trading signals and actionable insights.

### Key Features
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
```
ALPHA_VANTAGE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
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

See `VPS_SETUP.md` for deployment details.

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
| `POST /api/tickers` | Add a new ticker |
| `GET /api/tickers/{symbol}` | Get ticker details with news |
| `DELETE /api/tickers/{symbol}` | Remove a ticker |
| `GET /api/jobs/status` | Job tracker status |
| `POST /api/jobs/fetch` | Trigger news fetch manually |
| `POST /api/jobs/analyze` | Trigger analysis manually |

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
│ Alpha Vantage │    │  Gemini AI    │    │   SQLite      │
│ API + Cache   │    │  Analysis     │    │   Storage     │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        v                     v                     v
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    cache      │    │    models     │    │   exporter    │
│               │    │               │    │               │
│ File-based    │    │   Pydantic    │    │ JSON/CSV/HTML │
│ TTL caching   │    │   Validation  │    │   Reports     │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │
        v                     v
┌───────────────┐    ┌───────────────┐
│    config     │    │   scoring     │
│               │    │               │
│   Settings    │    │  Aggregation  │
│   from .env   │    │  & Signals    │
└───────────────┘    └───────────────┘
```

---

## Module Reference

### Core Modules

| Module | Purpose |
|--------|---------|
| `main.py` | CLI entry point, argument parsing, display |
| `news_retriever.py` | Alpha Vantage API integration with caching |
| `ia_analisis.py` | Gemini AI sentiment analysis |
| `database.py` | SQLite persistence |
| `models.py` | Pydantic data models |
| `config.py` | Configuration management |

### Feature Modules

| Module | Purpose |
|--------|---------|
| `cache.py` | File-based API response caching |
| `exporter.py` | JSON, CSV, HTML export |
| `scoring.py` | Sentiment aggregation and trading signals |
| `logger.py` | Structured logging with Rich |

### Test Modules

| Module | Purpose |
|--------|---------|
| `tests/test_models.py` | Model validation tests |
| `tests/test_config.py` | Configuration tests |
| `tests/test_news_retriever.py` | API integration tests |

---

## Data Models

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
├── news_retriever.py    # Alpha Vantage API
├── ia_analisis.py       # Gemini AI analysis
├── database.py          # SQLite persistence
├── cache.py             # API caching
├── exporter.py          # Export functionality
├── scoring.py           # Sentiment scoring
├── logger.py            # Logging configuration
├── requirements.txt     # Dependencies
├── .env                 # API keys (not in git)
├── .env.example         # Template for .env
├── .gitignore           # Git exclusions
├── CLAUDE.md            # This file
├── IMPROVEMENTS.md      # Improvement roadmap
└── tests/
    ├── __init__.py
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

The tool handles rate limiting automatically with `ratelimit` and `tenacity` libraries.

### Alpha Vantage NEWS_SENTIMENT Parameters

The API supports querying news **without specifying a ticker** using topics:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `function` | Yes | `NEWS_SENTIMENT` |
| `apikey` | Yes | API key |
| `tickers` | No | Filter by stock/crypto/forex symbols |
| `topics` | No | Filter by news categories |
| `time_from` / `time_to` | No | Date range (format: YYYYMMDDTHHMM) |
| `sort` / `limit` | No | Sort order and max results |

**Available topics:**
`blockchain`, `earnings`, `ipo`, `mergers_and_acquisitions`, `financial_markets`, `economy_fiscal`, `economy_monetary`, `economy_macro`, `energy_transportation`, `finance`, `life_sciences`, `manufacturing`, `real_estate`, `retail_wholesale`, `technology`

> **Note:** Currently the app always requires a ticker. A future enhancement could allow topic-based queries without a specific ticker.

---

## Future Enhancements

See `IMPROVEMENTS.md` for detailed roadmap. Key items:
- Real-time monitoring with alerts
- Backtesting framework
- Multi-source news integration (Reuters, Bloomberg)
- Web dashboard (Streamlit)
- Docker containerization
- Historical price correlation
- Topic-based news queries (without requiring a specific ticker)

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
