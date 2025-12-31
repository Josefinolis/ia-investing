# Migration Guide

This guide explains how to upgrade your existing ia_trading installation to use the new features.

---

## Prerequisites

- Python 3.11 or higher
- Existing ia_trading installation
- PostgreSQL server (optional, for database migration)

---

## Step 1: Update Dependencies

Install the new PostgreSQL driver:

```bash
cd /home/os_uis/projects/ia_trading
pip install -r requirements.txt
```

This will install `psycopg2-binary>=2.9.0` and all other dependencies.

---

## Step 2: Database Migration (Optional)

### Option A: Continue Using SQLite (No Changes Needed)

If you want to continue using SQLite, you don't need to do anything. The application will automatically use SQLite if `DATABASE_URL` is not set.

### Option B: Migrate to PostgreSQL

#### 2.1 Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ia_trading;

# Create user (optional)
CREATE USER ia_trading_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ia_trading TO ia_trading_user;

\q
```

#### 2.2 Set DATABASE_URL Environment Variable

Add to your `.env` file:

```bash
DATABASE_URL=postgresql://ia_trading_user:your_secure_password@localhost:5432/ia_trading
```

Or export as environment variable:

```bash
export DATABASE_URL="postgresql://ia_trading_user:your_secure_password@localhost:5432/ia_trading"
```

#### 2.3 Initialize PostgreSQL Database

```bash
# The tables will be created automatically on first run
python3 -c "from database import get_database; db = get_database(); db.init_db(); print('Database initialized')"
```

#### 2.4 Migrate Data from SQLite (Optional)

If you want to migrate existing data from SQLite to PostgreSQL:

```bash
# Export from SQLite
sqlite3 ia_trading.db .dump > ia_trading_sqlite_backup.sql

# Import to PostgreSQL (requires manual schema mapping)
# This is complex - contact support for assistance
```

**Note:** Automatic data migration is not included. For production migrations, consider using tools like `pgloader` or writing a custom migration script.

---

## Step 3: Verify Installation

### 3.1 Test Imports

```bash
python3 -c "from rate_limit_manager import get_rate_limit_manager; print('✓ Rate limit manager OK')"
python3 -c "from config import get_settings; print('✓ Config OK')"
python3 -c "from database import get_database; print('✓ Database OK')"
```

### 3.2 Test Database Connection

```bash
python3 -c "
from database import get_database
db = get_database()
db.init_db()
print('✓ Database connected and initialized')
"
```

You should see either "Using PostgreSQL database" or "Using SQLite database" in the output.

### 3.3 Start API Server

```bash
uvicorn api.main:app --reload --port 8000
```

Check the logs for:
- "Using PostgreSQL database" or "Using SQLite database"
- "Database initialized"
- "Rate limit manager initialized"

### 3.4 Test API Status Endpoint

```bash
curl http://localhost:8000/api/status
```

Expected response:
```json
{
  "gemini": {
    "available": true,
    "cooldown_until": null,
    "message": null
  },
  "alpha_vantage": {
    "available": true,
    "cooldown_until": null,
    "message": null
  }
}
```

---

## Step 4: Testing Rate Limit Handling

### 4.1 Add a Ticker

```bash
curl -X POST http://localhost:8000/api/tickers \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "name": "Apple Inc."}'
```

### 4.2 Trigger News Fetch

```bash
curl -X POST http://localhost:8000/api/tickers/AAPL/fetch?hours=24
```

### 4.3 Monitor Rate Limit Status

```bash
# Check status every few seconds
watch -n 2 curl -s http://localhost:8000/api/status
```

### 4.4 Simulate Rate Limit

To test the rate limit handling, you can temporarily reduce the rate limits in the code:

```python
# In ia_analisis.py, change line 41:
@limits(calls=2, period=60)  # Reduce from 15 to 2 for testing

# In news_retriever.py, change line 23:
@limits(calls=2, period=60)  # Reduce from 5 to 2 for testing
```

Then trigger multiple requests to hit the limit.

---

## Step 5: Monitor Logs

The application now logs all rate limit events:

```bash
# Start the API server with logging
uvicorn api.main:app --reload --log-level info

# Or view the logs in real-time
tail -f /path/to/logfile.log
```

Look for log messages like:
- "Gemini API in cooldown, 45s remaining. Skipping analysis."
- "Alpha Vantage API in cooldown, 30s remaining. Skipping fetch."
- "Gemini entering cooldown for 60s: Rate limit exceeded (429)"
- "Alpha Vantage entering cooldown for 60s: Rate limit exceeded"
- "Gemini cooldown cleared"

---

## Step 6: Production Deployment

### 6.1 Environment Variables

Create a `.env` file for production:

```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
GEMINI_API_KEY=your_gemini_key

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@db-server:5432/ia_trading

# Optional: Logging
LOG_LEVEL=INFO
```

### 6.2 Docker Deployment (Optional)

If using Docker, add to your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ia_trading
      POSTGRES_USER: ia_trading_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://ia_trading_user:${DB_PASSWORD}@postgres:5432/ia_trading
      ALPHA_VANTAGE_API_KEY: ${ALPHA_VANTAGE_API_KEY}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### 6.3 Systemd Service (Linux)

Create `/etc/systemd/system/ia-trading.service`:

```ini
[Unit]
Description=IA Trading API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/os_uis/projects/ia_trading
Environment="DATABASE_URL=postgresql://user:password@localhost:5432/ia_trading"
EnvironmentFile=/home/os_uis/projects/ia_trading/.env
ExecStart=/usr/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ia-trading
sudo systemctl start ia-trading
sudo systemctl status ia-trading
```

---

## Troubleshooting

### Database Connection Issues

**Error:** "could not connect to server: Connection refused"

**Solution:**
- Check PostgreSQL is running: `systemctl status postgresql`
- Verify connection string in DATABASE_URL
- Check firewall rules: `sudo ufw allow 5432/tcp`
- Test connection: `psql "postgresql://user:password@host:5432/ia_trading"`

### Import Errors

**Error:** "ModuleNotFoundError: No module named 'rate_limit_manager'"

**Solution:**
- Ensure you're in the project directory
- Check file exists: `ls -la rate_limit_manager.py`
- Verify Python path: `python3 -c "import sys; print(sys.path)"`

### Rate Limit Not Working

**Issue:** API calls continue even during cooldown

**Solution:**
- Check logs for cooldown messages
- Verify rate_limit_manager is imported correctly
- Test status endpoint: `curl http://localhost:8000/api/status`
- Restart the API server

### Database Migration Issues

**Issue:** Data not showing after migration

**Solution:**
- Verify tables created: `\dt` in psql
- Check database URL is correct
- Run init_db: `python3 -c "from database import get_database; get_database().init_db()"`
- Check for errors in logs

---

## Rollback Procedure

If you need to rollback the changes:

### 1. Restore Code

```bash
git checkout HEAD~1  # or your previous commit
```

### 2. Restore Database

```bash
# If using SQLite (backup exists)
cp ia_trading.db.backup ia_trading.db

# If using PostgreSQL
dropdb ia_trading
createdb ia_trading
psql ia_trading < backup.sql
```

### 3. Reinstall Dependencies

```bash
pip install -r requirements.txt
```

---

## Support

For issues or questions:
- Check logs for detailed error messages
- Review IMPLEMENTATION_SUMMARY.md for technical details
- Test with minimal configuration first
- Verify all dependencies are installed

---

## Next Steps

After successful migration:

1. Monitor the `/api/status` endpoint in your monitoring system
2. Set up alerts for rate limit events
3. Review and adjust cooldown durations if needed
4. Consider implementing persistent cooldown state (see IMPLEMENTATION_SUMMARY.md)
5. Optimize database performance (indexes, connection pooling)

Congratulations! Your ia_trading installation is now upgraded with PostgreSQL support and intelligent rate limit handling.
