# IA Trading - Development Context

Python API for stock sentiment analysis using Gemini AI.

## Architecture

```
main.py (CLI) ──┬── news_retriever.py ── news_sources/
                │                         ├── alpha_vantage.py
                │                         ├── reddit.py
                │                         └── twitter.py
                ├── ia_analisis.py (Gemini AI)
                └── database.py (PostgreSQL/SQLite)

api/main.py (FastAPI) ── services/ ── schedulers/
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `api/main.py` | FastAPI REST API |
| `news_retriever.py` | Multi-source news aggregation |
| `ia_analisis.py` | Gemini AI sentiment analysis |
| `database.py` | PostgreSQL (prod) / SQLite (dev) |
| `rate_limit_manager.py` | API rate limit handling |
| `scoring.py` | Trading signal calculation |

## Configuration (.env)

```bash
# Required
ALPHA_VANTAGE_API_KEY=xxx
GEMINI_API_KEY=xxx
DATABASE_URL=postgresql://user:pass@host:5432/ia_trading

# Optional
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
TWITTER_ENABLED=false
SCHEDULER_ENABLED=false
```

## Commands

```bash
# Development
uvicorn api.main:app --reload --port 8000

# CLI
python main.py AAPL --score

# Tests
pytest tests/ -v
```

## Production

- **URL:** http://195.20.235.94
- **Deploy:** Push to `master` triggers GitHub Actions
- **Infrastructure:** https://github.com/Josefinolis/documentation

## Concurrency & Performance

The API uses **4 uvicorn workers** to handle concurrent requests. This prevents a blocked worker from freezing the entire server.

### News Scrapers

Scrapers run in parallel using `ThreadPoolExecutor` with a **30-second timeout** per source:

| Source | Status | Notes |
|--------|--------|-------|
| Alpha Vantage | Active | Rate limited (5/min) |
| Reddit | Active | Via ntscraper (blocking) |
| Twitter | Active | Via ntscraper (blocking) |

The `news_sources/aggregator.py` wraps blocking scrapers in threads to prevent them from freezing the API.

### Configuration

```bash
# Enable/disable scrapers in deployment
TWITTER_ENABLED=true
SCHEDULER_ENABLED=false
```

## Rate Limits

| Service | Limit | Cooldown |
|---------|-------|----------|
| Alpha Vantage | 5/min | 60s auto |
| Gemini | 15 RPM | 60s auto |

Check `/api/status` endpoint for current rate limit state.
