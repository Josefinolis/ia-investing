"""API endpoints for manual job triggers."""

import threading
from typing import Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from services.job_tracker import get_job_tracker
from logger import logger


router = APIRouter()


class JobTriggerResponse(BaseModel):
    """Response for job trigger requests."""
    message: str
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    """Response for job status requests."""
    jobs: Dict[str, Any]


def run_fetch_all_news():
    """Background task to fetch news for all tickers."""
    from schedulers.news_fetcher import fetch_all_news_job
    import time

    job_id = "fetch_all_news"
    tracker = get_job_tracker()

    # Check if already running
    if tracker.is_job_running(job_id):
        logger.warning(f"Job {job_id} is already running, skipping")
        return

    tracker.start_job(job_id)
    logger.info(f"Manual trigger: Starting {job_id}")

    start_time = time.perf_counter()
    error = None

    try:
        result = fetch_all_news_job()
        duration = time.perf_counter() - start_time
        tracker.complete_job(job_id, duration, result)
        logger.info(f"Manual trigger: Completed {job_id} in {duration:.3f}s")
    except Exception as e:
        duration = time.perf_counter() - start_time
        error = str(e)
        tracker.complete_job(job_id, duration, error=error)
        logger.error(f"Manual trigger: Failed {job_id}: {e}")


def run_fetch_news_ticker(ticker: str):
    """Background task to fetch news for a specific ticker."""
    from schedulers.news_fetcher import fetch_news_for_ticker
    import time

    job_id = "fetch_news_ticker"
    tracker = get_job_tracker()

    # Allow concurrent runs for different tickers
    tracker.start_job(job_id)
    logger.info(f"Manual trigger: Starting {job_id} for {ticker}")

    start_time = time.perf_counter()
    error = None

    try:
        result = fetch_news_for_ticker(ticker, hours=24)
        duration = time.perf_counter() - start_time
        tracker.complete_job(job_id, duration, result)
        logger.info(f"Manual trigger: Completed {job_id} for {ticker} in {duration:.3f}s")
    except Exception as e:
        duration = time.perf_counter() - start_time
        error = str(e)
        tracker.complete_job(job_id, duration, error=error)
        logger.error(f"Manual trigger: Failed {job_id} for {ticker}: {e}")


def run_analyze_pending():
    """Background task to analyze pending news."""
    from schedulers.analyzer import analyze_all_pending
    import time

    job_id = "analyze_pending"
    tracker = get_job_tracker()

    # Check if already running
    if tracker.is_job_running(job_id):
        logger.warning(f"Job {job_id} is already running, skipping")
        return

    tracker.start_job(job_id)
    logger.info(f"Manual trigger: Starting {job_id}")

    start_time = time.perf_counter()
    error = None

    try:
        result = analyze_all_pending()
        duration = time.perf_counter() - start_time
        tracker.complete_job(job_id, duration, result)
        logger.info(f"Manual trigger: Completed {job_id} in {duration:.3f}s")
    except Exception as e:
        duration = time.perf_counter() - start_time
        error = str(e)
        tracker.complete_job(job_id, duration, error=error)
        logger.error(f"Manual trigger: Failed {job_id}: {e}")


@router.post("/fetch-news", response_model=JobTriggerResponse)
async def trigger_fetch_news(background_tasks: BackgroundTasks):
    """
    Manually trigger news fetch for all tickers in watchlist.

    Runs in background and returns immediately.
    Use GET /api/jobs/status to check progress.
    """
    tracker = get_job_tracker()

    # Check if already running
    if tracker.is_job_running("fetch_all_news"):
        raise HTTPException(
            status_code=409,
            detail="News fetch job is already running. Check /api/jobs/status for progress."
        )

    # Queue the background task
    background_tasks.add_task(run_fetch_all_news)

    return JobTriggerResponse(
        message="News fetch job started in background",
        job_id="fetch_all_news",
        status="running"
    )


@router.post("/fetch-news/{symbol}", response_model=JobTriggerResponse)
async def trigger_fetch_news_ticker(symbol: str, background_tasks: BackgroundTasks):
    """
    Manually trigger news fetch for a specific ticker.

    Runs in background and returns immediately.
    Use GET /api/jobs/status to check progress.

    Args:
        symbol: Stock ticker symbol (e.g., AAPL, TSLA)
    """
    ticker = symbol.upper()

    # Queue the background task
    background_tasks.add_task(run_fetch_news_ticker, ticker)

    return JobTriggerResponse(
        message=f"News fetch job for {ticker} started in background",
        job_id="fetch_news_ticker",
        status="running"
    )


@router.post("/analyze", response_model=JobTriggerResponse)
async def trigger_analyze(background_tasks: BackgroundTasks):
    """
    Manually trigger sentiment analysis for all pending news.

    Runs in background and returns immediately.
    Use GET /api/jobs/status to check progress.
    """
    tracker = get_job_tracker()

    # Check if already running
    if tracker.is_job_running("analyze_pending"):
        raise HTTPException(
            status_code=409,
            detail="Analysis job is already running. Check /api/jobs/status for progress."
        )

    # Queue the background task
    background_tasks.add_task(run_analyze_pending)

    return JobTriggerResponse(
        message="Analysis job started in background",
        job_id="analyze_pending",
        status="running"
    )


@router.get("/status", response_model=JobStatusResponse)
async def get_jobs_status():
    """
    Get status of all background jobs.

    Returns:
        - job_id: Unique job identifier
        - status: idle, running, completed, or failed
        - last_run_time: When the job last started
        - last_duration: How long the last run took (seconds)
        - last_result: Results from the last run
        - error: Error message if last run failed
    """
    tracker = get_job_tracker()
    all_status = tracker.get_all_status()

    return JobStatusResponse(jobs=all_status)
