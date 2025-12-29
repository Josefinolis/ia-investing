"""APScheduler setup and management."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from logger import logger

# Global scheduler instance
_scheduler: BackgroundScheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def start_scheduler():
    """Start the scheduler with all jobs."""
    from schedulers.news_fetcher import fetch_all_news_job
    from schedulers.analyzer import analyze_pending_news_job

    scheduler = get_scheduler()

    if scheduler.running:
        logger.info("Scheduler already running")
        return

    # Add news fetcher job - every 30 minutes
    scheduler.add_job(
        fetch_all_news_job,
        trigger=IntervalTrigger(minutes=30),
        id="news_fetcher",
        name="Fetch news for all tickers",
        replace_existing=True
    )

    # Add analyzer job - every 5 minutes
    scheduler.add_job(
        analyze_pending_news_job,
        trigger=IntervalTrigger(minutes=5),
        id="news_analyzer",
        name="Analyze pending news",
        replace_existing=True
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
