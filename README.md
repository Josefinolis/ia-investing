# IA Trading - Market Sentiment Analysis

Python API that analyzes news sentiment for stocks using AI to generate trading signals.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure (.env)
ALPHA_VANTAGE_API_KEY=your_key
GEMINI_API_KEY=your_key

# Run API
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Swagger documentation |
| `/api/tickers` | GET | List tracked tickers |
| `/api/tickers` | POST | Add ticker |
| `/api/tickers/{symbol}` | GET | Get ticker with news |
| `/api/tickers/{symbol}/fetch` | POST | Fetch news for ticker |
| `/api/tickers/{symbol}/analyze` | POST | Analyze ticker sentiment |
| `/api/status` | GET | API rate limit status |

## CLI Usage

```bash
python main.py AAPL --score          # Analyze with trading signal
python main.py TSLA --days 30        # Custom date range
python main.py AAPL,MSFT --score     # Batch analysis
python main.py AAPL --export json    # Export results
```

## Trading Signals

| Signal | Score Range |
|--------|-------------|
| STRONG BUY | >= +0.5 |
| BUY | >= +0.2 |
| HOLD | -0.2 to +0.2 |
| SELL | <= -0.2 |
| STRONG SELL | <= -0.5 |

## Production

- **URL:** http://195.20.235.94
- **Docs:** http://195.20.235.94/docs
- **Infrastructure:** https://github.com/Josefinolis/documentation

Deployment is automatic via GitHub Actions on push to `master`.

## Rate Limits

| Service | Limit |
|---------|-------|
| Alpha Vantage | 5 calls/min |
| Gemini | 15 RPM |

Rate limiting is handled automatically with 60s cooldown.
