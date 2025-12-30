"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import tickers
from api.schemas import HealthResponse, ApiStatusResponse, ApiServiceStatus
from database import get_database
from schedulers.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from rate_limit_manager import get_rate_limit_manager
from logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting IA Trading API...")

    # Initialize database
    db = get_database()
    db.init_db()
    logger.info("Database initialized")

    # Start scheduler
    start_scheduler()

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
    """Health check endpoint."""
    scheduler_status = get_scheduler_status()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="connected",
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
