"""FastAPI application entry point."""

import faulthandler
import gc
import os
import resource
import sys
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Enable faulthandler to dump tracebacks on SIGUSR1
faulthandler.enable()
if hasattr(faulthandler, 'register'):
    import signal
    faulthandler.register(signal.SIGUSR1, all_threads=True)

from api.routers import tickers, jobs
from api.schemas import HealthResponse, ApiStatusResponse, ApiServiceStatus
from database import get_database
from schedulers.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from rate_limit_manager import get_rate_limit_manager
from logger import logger
from config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    import time

    # Startup
    startup_start = time.perf_counter()
    logger.info("=" * 50)
    logger.info("Starting IA Trading API...")
    logger.info("=" * 50)

    # Initialize database
    logger.info("[STARTUP] Connecting to database...")
    db_start = time.perf_counter()
    db = get_database()
    db_connect_elapsed = time.perf_counter() - db_start
    logger.info(f"[STARTUP] Database connection established in {db_connect_elapsed:.3f}s")

    logger.info("[STARTUP] Initializing database tables...")
    init_start = time.perf_counter()
    db.init_db()
    init_elapsed = time.perf_counter() - init_start
    logger.info(f"[STARTUP] Database tables initialized in {init_elapsed:.3f}s")

    startup_elapsed = time.perf_counter() - startup_start
    logger.info(f"[STARTUP] Total startup time: {startup_elapsed:.3f}s")

    # Start scheduler (if enabled)
    settings = get_settings()
    if settings.scheduler_enabled:
        logger.info("Scheduler mode: ENABLED - Background jobs will run automatically")
        start_scheduler()
    else:
        logger.info("Scheduler mode: DISABLED - Use /api/jobs/* endpoints to trigger jobs manually")

    yield

    # Shutdown
    logger.info("Shutting down IA Trading API...")
    stop_scheduler()


app = FastAPI(
    title="IA Trading API",
    description="Market Sentiment Analysis API - Analyze financial news sentiment using AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev
        "http://localhost:3000",  # React dev
        "http://10.0.2.2:8000",   # Android emulator
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickers.router, prefix="/api/tickers", tags=["tickers"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": "IA Trading API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint - lightweight, no DB call."""
    # Don't touch DB here to keep health check fast
    # This prevents Render from marking the service as unhealthy during cold starts
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="unknown",  # Don't check DB in health endpoint
        scheduler="unknown"
    )


@app.get("/health/full", response_model=HealthResponse, tags=["health"])
async def health_check_full():
    """Full health check with database verification."""
    scheduler_status = get_scheduler_status()

    # Test database connection
    from sqlalchemy import text
    db_status = "unknown"
    try:
        db = get_database()
        with db.get_session() as session:
            session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version="1.0.0",
        database=db_status,
        scheduler="running" if scheduler_status["running"] else "stopped"
    )


@app.get("/api/scheduler/status", tags=["scheduler"])
async def scheduler_status():
    """Get scheduler status and job information."""
    return get_scheduler_status()


@app.post("/api/scheduler/trigger/{job_id}", tags=["scheduler"])
async def trigger_job(job_id: str):
    """Manually trigger a scheduler job."""
    from schedulers.scheduler import trigger_job as do_trigger

    success = do_trigger(job_id)

    if success:
        return {"message": f"Job {job_id} triggered"}
    else:
        return {"error": f"Job {job_id} not found"}


@app.get("/api/status", response_model=ApiStatusResponse, tags=["status"])
async def api_status():
    """Get API rate limit status for all services."""
    rate_limiter = get_rate_limit_manager()
    status_data = rate_limiter.get_all_status()

    return ApiStatusResponse(
        gemini=ApiServiceStatus(**status_data["gemini"]),
        alpha_vantage=ApiServiceStatus(**status_data["alpha_vantage"])
    )


@app.get("/debug/status", tags=["debug"])
async def debug_status():
    """Debug endpoint showing system resource usage."""
    import psutil

    process = psutil.Process()

    # Thread info
    all_threads = threading.enumerate()
    thread_info = [
        {"name": t.name, "alive": t.is_alive(), "daemon": t.daemon}
        for t in all_threads
    ]

    # Memory info
    mem_info = process.memory_info()

    # File descriptors
    try:
        fd_count = len(process.open_files())
        connections = len(process.connections())
    except Exception:
        fd_count = -1
        connections = -1

    # Database pool info
    db_pool_info = {}
    try:
        db = get_database()
        if hasattr(db, '_engine') and db._engine:
            pool = db._engine.pool
            db_pool_info = {
                "size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "checked_in": pool.checkedin(),
            }
    except Exception as e:
        db_pool_info = {"error": str(e)}

    # Resource limits
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)

    return {
        "threads": {
            "count": len(all_threads),
            "details": thread_info
        },
        "memory": {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
        },
        "file_descriptors": {
            "open_files": fd_count,
            "connections": connections,
            "limit_soft": soft_limit,
            "limit_hard": hard_limit,
        },
        "database_pool": db_pool_info,
        "gc": {
            "objects": len(gc.get_objects()),
            "garbage": len(gc.garbage),
        },
        "process": {
            "pid": os.getpid(),
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
        }
    }


@app.get("/debug/threads/dump", tags=["debug"])
async def dump_threads():
    """Dump stack traces of all threads."""
    import io
    import traceback

    output = io.StringIO()
    output.write(f"Thread dump at {__import__('datetime').datetime.now()}\n")
    output.write(f"Total threads: {threading.active_count()}\n\n")

    for thread_id, frame in sys._current_frames().items():
        thread_name = "Unknown"
        for t in threading.enumerate():
            if t.ident == thread_id:
                thread_name = t.name
                break

        output.write(f"--- Thread {thread_id} ({thread_name}) ---\n")
        output.write("".join(traceback.format_stack(frame)))
        output.write("\n")

    return {"dump": output.getvalue()}
