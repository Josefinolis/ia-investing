"""APScheduler setup and management."""

import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from logger import logger
from config import get_settings
from services.job_tracker import get_job_tracker

# Global scheduler instance
_scheduler: BackgroundScheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def _tracked_fetch_all_news():
    """Wrapper for fetch_all_news_job with job tracking."""
    from schedulers.news_fetcher import fetch_all_news_job

    job_id = "fetch_all_news"
    tracker = get_job_tracker()

    if tracker.is_job_running(job_id):
        logger.warning(f"Scheduled job {job_id} is already running, skipping")
        return

    tracker.start_job(job_id)
    start_time = time.perf_counter()
    error = None

    try:
        result = fetch_all_news_job()
        duration = time.perf_counter() - start_time
        tracker.complete_job(job_id, duration, result)
    except Exception as e:
        duration = time.perf_counter() - start_time
        error = str(e)
        tracker.complete_job(job_id, duration, error=error)
        logger.error(f"Scheduled job {job_id} failed: {e}")


def _tracked_analyze_pending():
    """Wrapper for analyze_pending_news_job with job tracking."""
    from schedulers.analyzer import analyze_pending_news_job

    job_id = "analyze_pending"
    tracker = get_job_tracker()

    if tracker.is_job_running(job_id):
        logger.warning(f"Scheduled job {job_id} is already running, skipping")
        return

    tracker.start_job(job_id)
    start_time = time.perf_counter()
    error = None

    try:
        result = analyze_pending_news_job()
        duration = time.perf_counter() - start_time
        tracker.complete_job(job_id, duration, result)
    except Exception as e:
        duration = time.perf_counter() - start_time
        error = str(e)
        tracker.complete_job(job_id, duration, error=error)
        logger.error(f"Scheduled job {job_id} failed: {e}")


def start_scheduler():
    """Start the scheduler with all jobs."""
    settings = get_settings()

    # Check if scheduler is enabled
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled by configuration (SCHEDULER_ENABLED=False)")
        logger.info("Jobs can still be triggered manually via API endpoints")
        return

    scheduler = get_scheduler()

    if scheduler.running:
        logger.info("Scheduler already running")
        return

    # Add news fetcher job - every 30 minutes
    scheduler.add_job(
        _tracked_fetch_all_news,
        trigger=IntervalTrigger(minutes=30),
        id="news_fetcher",
        name="Fetch news for all tickers",
        replace_existing=True
    )

    # Add analyzer job - every 5 minutes (only calls AI if there are pending news)
    scheduler.add_job(
        _tracked_analyze_pending,
        trigger=IntervalTrigger(minutes=5),
        id="news_analyzer",
        name="Analyze pending news",
        replace_existing=True,
        coalesce=True,  # Combine missed runs into one
        max_instances=1  # Only one instance at a time
    )

    scheduler.start()
    logger.info("Scheduler started with jobs: news_fetcher (30m), news_analyzer (5m)")


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def get_scheduler_status() -> dict:
    """Get scheduler status and job info."""
    scheduler = get_scheduler()
    jobs = []

    if scheduler.running:
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            })

    return {
        "running": scheduler.running,
        "jobs": jobs
    }


def trigger_job(job_id: str) -> bool:
    """Manually trigger a job."""
    from datetime import datetime

    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)

    if job:
        job.modify(next_run_time=datetime.now())  # Run immediately
        logger.info(f"Triggered job: {job_id}")
        return True

    return False
