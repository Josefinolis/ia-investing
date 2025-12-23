# IA Trading - Future Improvements

## Overview

This document lists potential future enhancements for the ia-trading project. The core functionality is now production-ready with sentiment analysis, trading signals, database persistence, caching, and export capabilities.

---

## HIGH PRIORITY

### 1. Backtesting Framework
**Effort**: 8-12 hours
**Value**: Validate sentiment signals against historical price movements

**Implementation Ideas**:
```python
# backtester.py
class Backtester:
    def __init__(self, ticker: str, start_date: datetime, end_date: datetime):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date

    def fetch_price_data(self) -> pd.DataFrame:
        """Fetch historical OHLCV data from Alpha Vantage"""
        pass

    def correlate_sentiment_with_returns(self) -> dict:
        """Calculate correlation between sentiment and next-day returns"""
        pass

    def generate_report(self) -> BacktestReport:
        """Generate backtesting performance report"""
        pass
```

**Features**:
- Fetch historical price data (Alpha Vantage TIME_SERIES_DAILY)
- Calculate next-day, 3-day, 7-day returns after sentiment signals
- Measure signal accuracy and profitability
- Generate performance metrics (Sharpe ratio, win rate, etc.)

**Dependencies**: `pandas`, `numpy`

---

### 2. Multi-Source News Integration
**Effort**: 6-8 hours
**Value**: More comprehensive sentiment analysis with multiple news sources

**Potential Sources**:
- **NewsAPI** (newsapi.org) - General news aggregator
- **Finnhub** (finnhub.io) - Financial news with sentiment scores
- **Polygon.io** - Real-time market data and news
- **RSS Feeds** - Reuters, Bloomberg, CNBC

**Implementation Ideas**:
```python
# news_sources/base.py
class NewsSource(ABC):
    @abstractmethod
    def fetch_news(self, ticker: str, from_date: datetime, to_date: datetime) -> List[NewsItem]:
        pass

# news_sources/finnhub.py
class FinnhubSource(NewsSource):
    def fetch_news(self, ticker, from_date, to_date):
        # Implementation
        pass

# news_aggregator.py
class NewsAggregator:
    def __init__(self, sources: List[NewsSource]):
        self.sources = sources

    def fetch_all(self, ticker, from_date, to_date) -> List[NewsItem]:
        """Fetch and deduplicate news from all sources"""
        pass
```

---

### 3. Real-Time Monitoring & Alerts
**Effort**: 10-15 hours
**Value**: Proactive notifications when sentiment changes significantly

**Features**:
- Scheduled analysis (every 15 min, hourly, daily)
- Alert thresholds (e.g., sentiment drops below -0.5)
- Multiple notification channels (email, Slack, Telegram)
- Watchlist management

**Implementation Ideas**:
```python
# monitor.py
class SentimentMonitor:
    def __init__(self, watchlist: List[str], interval_minutes: int = 15):
        self.watchlist = watchlist
        self.interval = interval_minutes
        self.alert_handlers = []

    def add_alert_handler(self, handler: AlertHandler):
        self.alert_handlers.append(handler)

    async def run(self):
        """Run continuous monitoring loop"""
        while True:
            for ticker in self.watchlist:
                score = await self.analyze(ticker)
                if self.should_alert(score):
                    await self.send_alerts(ticker, score)
            await asyncio.sleep(self.interval * 60)

# alerts/slack.py
class SlackAlertHandler(AlertHandler):
    def send(self, ticker: str, score: SentimentScore, message: str):
        # Send to Slack webhook
        pass
```

**Dependencies**: `schedule` or `apscheduler`, `aiohttp`, `slack-sdk`

---

## MEDIUM PRIORITY

### 4. Web Dashboard (Streamlit)
**Effort**: 8-10 hours
**Value**: Visual interface for non-technical users

**Features**:
- Ticker search and selection
- Interactive date range picker
- Sentiment charts and visualizations
- Historical trend analysis
- Export functionality

**Implementation**:
```python
# dashboard.py
import streamlit as st

st.title("IA Trading - Sentiment Dashboard")

ticker = st.text_input("Enter ticker symbol", "AAPL")
days = st.slider("Days to analyze", 1, 90, 7)

if st.button("Analyze"):
    with st.spinner("Analyzing..."):
        results = run_analysis(ticker, days)

    st.metric("Sentiment Score", f"{results.score:+.2f}")
    st.metric("Signal", results.signal)

    # Sentiment distribution chart
    st.bar_chart(results.distribution)
```

**Run with**: `streamlit run dashboard.py`

**Dependencies**: `streamlit`, `plotly`

---

### 5. Docker Containerization
**Effort**: 2-4 hours
**Value**: Easy deployment and reproducible environment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "main.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  ia-trading:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./exports:/app/exports
      - ./.cache:/app/.cache
```

**Usage**:
```bash
docker build -t ia-trading .
docker run --env-file .env ia-trading AAPL --score
```

---

### 6. Historical Price Correlation
**Effort**: 6-8 hours
**Value**: Validate if sentiment predicts price movements

**Features**:
- Fetch historical price data alongside news
- Calculate correlation coefficients
- Identify leading/lagging indicators
- Generate correlation reports

**Implementation Ideas**:
```python
# correlation.py
def calculate_sentiment_price_correlation(
    ticker: str,
    sentiment_scores: List[SentimentScore],
    price_data: pd.DataFrame,
    lag_days: int = 1
) -> CorrelationResult:
    """
    Calculate correlation between sentiment and price changes.

    Args:
        lag_days: Days to look ahead for price change (1 = next day)
    """
    pass
```

---

## LOWER PRIORITY

### 7. Portfolio Analysis
**Effort**: 6-8 hours
**Value**: Analyze sentiment across entire portfolio

**Features**:
- Import portfolio from CSV/broker API
- Weighted sentiment score by position size
- Portfolio-level signals
- Risk assessment based on sentiment divergence

---

### 8. Sentiment History Visualization
**Effort**: 4-6 hours
**Value**: Track sentiment changes over time

**Features**:
- Time-series charts of sentiment scores
- Compare sentiment vs price movements
- Identify sentiment regime changes
- Export charts as images

**Dependencies**: `matplotlib`, `plotly`

---

### 9. Natural Language Insights
**Effort**: 4-6 hours
**Value**: Generate human-readable market summaries

**Features**:
- Daily/weekly sentiment summaries
- Key themes extraction
- Notable news highlights
- AI-generated market commentary

---

### 10. API Server Mode
**Effort**: 6-8 hours
**Value**: Enable integration with other applications

**Features**:
- REST API endpoints
- Authentication
- Rate limiting
- Webhook notifications

**Implementation**:
```python
# api.py
from fastapi import FastAPI

app = FastAPI(title="IA Trading API")

@app.get("/analyze/{ticker}")
async def analyze_ticker(ticker: str, days: int = 7):
    results = await run_analysis(ticker, days)
    return results.to_dict()

@app.get("/score/{ticker}")
async def get_score(ticker: str):
    score = await calculate_score(ticker)
    return score.to_dict()
```

**Dependencies**: `fastapi`, `uvicorn`

---

## Implementation Checklist

When implementing any improvement:

- [ ] Write unit tests first (TDD)
- [ ] Update requirements.txt with new dependencies
- [ ] Add configuration options to config.py
- [ ] Update CLI arguments in main.py if needed
- [ ] Document in README.md
- [ ] Update CLAUDE.md with architecture changes

---

## Contributing

1. Pick an improvement from this list
2. Create a feature branch: `git checkout -b feature/improvement-name`
3. Implement with tests
4. Update documentation
5. Submit for review

---

*Last updated: 2024-12-23*
