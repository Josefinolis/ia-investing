# IA Trading - Market Sentiment Analysis Tool

A Python CLI tool that analyzes news sentiment for stocks using AI to identify trading opportunities.

## Features

- **Sentiment Analysis**: Classifies news into 5 categories (Highly Negative → Highly Positive)
- **Trading Signals**: STRONG BUY, BUY, HOLD, SELL, STRONG SELL based on aggregated sentiment
- **Batch Processing**: Analyze multiple tickers at once
- **Data Persistence**: SQLite database for historical analysis
- **Export**: JSON, CSV, and HTML reports
- **Caching**: Reduces API calls with intelligent caching
- **Rate Limiting**: Automatic handling of API quotas

## Prerequisites

- Python 3.10+
- Alpha Vantage API key (free: https://www.alphavantage.co/support/#api-key)
- Google Gemini API key (free: https://aistudio.google.com/apikey)

## Installation

### 1. Clone and Setup

```bash
cd /home/os_uis/projects/ia_trading

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
```

Your `.env` file should contain:
```
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
GEMINI_API_KEY=your_gemini_key_here
```

## Running from Terminal

### Basic Usage

```bash
# Analyze a single ticker (last 7 days)
python main.py AAPL

# Analyze with custom date range
python main.py TSLA --days 30
python main.py MSFT --from 2024-01-01 --to 2024-12-31

# Show trading signal and score
python main.py NVDA --score

# Analyze multiple tickers
python main.py AAPL,MSFT,GOOGL,AMZN --score

# Save results to database
python main.py AAPL --save

# View historical analysis
python main.py AAPL --summary

# Export results
python main.py TSLA --export json
python main.py NVDA --export csv
python main.py AAPL --export html

# Fetch news only (no AI analysis)
python main.py AAPL --no-analyze

# Skip cache (fresh data)
python main.py TSLA --no-cache

# Limit number of news items
python main.py AAPL --limit 20
```

### CLI Options Reference

| Option | Description |
|--------|-------------|
| `ticker` | Stock symbol(s), comma-separated for batch |
| `--days N` | Look back N days (default: 7) |
| `--from DATE` | Start date (YYYY-MM-DD) |
| `--to DATE` | End date (YYYY-MM-DD) |
| `--score` | Show sentiment score and trading signal |
| `--save` | Save results to SQLite database |
| `--summary` | Show historical summary from database |
| `--export FORMAT` | Export to json, csv, or html |
| `--batch` | Enable batch mode for multiple tickers |
| `--limit N` | Max news items to analyze (default: 50) |
| `--no-cache` | Disable caching |
| `--no-analyze` | Fetch news only |
| `-v, --verbose` | Verbose output |

## Running from VS Code

### Option 1: Integrated Terminal

1. Open the project folder in VS Code
2. Open terminal: `Ctrl+`` ` (backtick) or `View → Terminal`
3. Activate virtual environment:
   ```bash
   source venv/bin/activate  # Linux/Mac
   ```
4. Run commands as shown above

### Option 2: Run and Debug (launch.json)

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Analyze AAPL",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["AAPL", "--score"],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Analyze with Custom Args",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["${input:ticker}", "--days", "${input:days}", "--score"],
            "console": "integratedTerminal"
        },
        {
            "name": "Batch Analysis",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["AAPL,MSFT,GOOGL", "--score", "--export", "html"],
            "console": "integratedTerminal"
        },
        {
            "name": "Run Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ],
    "inputs": [
        {
            "id": "ticker",
            "type": "promptString",
            "description": "Enter ticker symbol(s)",
            "default": "AAPL"
        },
        {
            "id": "days",
            "type": "promptString",
            "description": "Number of days to analyze",
            "default": "7"
        }
    ]
}
```

Then press `F5` or go to `Run → Start Debugging` to run.

### Option 3: Python Extension Run Button

1. Open `main.py`
2. Click the "Run Python File" button (▶️) in the top-right
3. Or right-click and select "Run Python File in Terminal"

Note: This runs without arguments. For custom arguments, use the terminal or launch.json.

### VS Code Recommended Extensions

- **Python** (ms-python.python) - Required
- **Pylance** (ms-python.vscode-pylance) - IntelliSense
- **Python Debugger** (ms-python.debugpy) - Debugging

### VS Code Settings (settings.json)

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.analysis.typeCheckingMode": "basic"
}
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

## Project Structure

```
ia_trading/
├── main.py              # CLI entry point
├── config.py            # Configuration (from .env)
├── models.py            # Pydantic data models
├── news_retriever.py    # Alpha Vantage API client
├── ia_analisis.py       # Gemini AI analysis
├── database.py          # SQLite persistence
├── cache.py             # API response caching
├── exporter.py          # Export (JSON/CSV/HTML)
├── scoring.py           # Sentiment scoring & signals
├── logger.py            # Logging configuration
├── requirements.txt     # Dependencies
├── .env                 # API keys (not in git)
├── .env.example         # Template for .env
└── tests/               # Unit tests
```

## Output Examples

### Single Ticker Analysis
```
╭─────────── IA Trading ───────────╮
│ Analyzing sentiment for AAPL     │
│ Period: 2024-12-16 to 2024-12-23 │
╰──────────────────────────────────╯

Found 15 news items

┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Date       ┃ Source         ┃ Title                                       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2024-12-23 │ Reuters        │ Apple announces new product launch...       │
│ 2024-12-22 │ Bloomberg      │ Tech stocks rally amid holiday season...    │
└────────────┴────────────────┴─────────────────────────────────────────────┘

╭───────── Score Analysis ─────────╮
│ AAPL Sentiment Score             │
╰──────────────────────────────────╯
Signal: BUY ↑
Sentiment: Positive
Score: +0.35 (scale: -1 to +1)
Confidence: 72.5%
```

### Trading Signals

| Signal | Score Range | Meaning |
|--------|-------------|---------|
| STRONG BUY | >= +0.5 | Highly positive sentiment |
| BUY | >= +0.2 | Positive sentiment |
| HOLD | -0.2 to +0.2 | Neutral sentiment |
| SELL | <= -0.2 | Negative sentiment |
| STRONG SELL | <= -0.5 | Highly negative sentiment |

## Troubleshooting

### "Configuration error"
- Ensure `.env` file exists with valid API keys
- Check that keys don't have extra spaces or quotes

### "No news items found"
- Try a different ticker symbol
- Extend the date range: `--days 30`
- Some tickers may have limited news coverage

### "API rate limit exceeded"
- Wait 60 seconds between runs
- Use `--limit` to reduce requests
- Results are cached by default (use `--no-cache` to refresh)

### Import errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

## API Rate Limits

| Service | Free Tier |
|---------|-----------|
| Alpha Vantage | 5 calls/min, 500 calls/day |
| Gemini | 15 RPM, 1M tokens/min |

The tool handles rate limiting automatically.

## License

MIT License
