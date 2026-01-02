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

## Rate Limits

| Service | Limit | Cooldown |
|---------|-------|----------|
| Alpha Vantage | 5/min | 60s auto |
| Gemini | 15 RPM | 60s auto |

Check `/api/status` endpoint for current rate limit state.
