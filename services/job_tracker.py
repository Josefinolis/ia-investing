"""Job tracker for monitoring background job execution."""

import threading
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobInfo:
    """Information about a job execution."""
    job_id: str
    status: JobStatus
    last_run_time: Optional[datetime] = None
    last_duration: Optional[float] = None
    last_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime to ISO format string
        if self.last_run_time:
            data['last_run_time'] = self.last_run_time.isoformat()
        # Convert enum to string
        data['status'] = self.status.value
        return data


class JobTracker:
    """Thread-safe job execution tracker."""

    def __init__(self):
        self._jobs: Dict[str, JobInfo] = {}
        self._lock = threading.Lock()

        # Initialize known jobs
        self._jobs["fetch_all_news"] = JobInfo(
            job_id="fetch_all_news",
            status=JobStatus.IDLE
        )
        self._jobs["fetch_news_ticker"] = JobInfo(
            job_id="fetch_news_ticker",
            status=JobStatus.IDLE
        )
        self._jobs["analyze_pending"] = JobInfo(
            job_id="analyze_pending",
            status=JobStatus.IDLE
        )

    def start_job(self, job_id: str) -> None:
        """Mark a job as started."""
        with self._lock:
            if job_id not in self._jobs:
                self._jobs[job_id] = JobInfo(job_id=job_id, status=JobStatus.RUNNING)
            else:
                self._jobs[job_id].status = JobStatus.RUNNING
                self._jobs[job_id].last_run_time = datetime.now()
                self._jobs[job_id].error = None

    def complete_job(
        self,
        job_id: str,
        duration: float,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Mark a job as completed."""
        with self._lock:
            if job_id not in self._jobs:
                self._jobs[job_id] = JobInfo(job_id=job_id, status=JobStatus.IDLE)

            job = self._jobs[job_id]
            job.status = JobStatus.FAILED if error else JobStatus.IDLE
            job.last_duration = duration
            job.last_result = result
            job.error = error

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        with self._lock:
            job = self._jobs.get(job_id)
            return job.to_dict() if job else None

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all jobs."""
        with self._lock:
            return {job_id: job.to_dict() for job_id, job in self._jobs.items()}

    def is_job_running(self, job_id: str) -> bool:
        """Check if a job is currently running."""
        with self._lock:
            job = self._jobs.get(job_id)
            return job.status == JobStatus.RUNNING if job else False


# Global tracker instance
_tracker: Optional[JobTracker] = None
_tracker_lock = threading.Lock()


def get_job_tracker() -> JobTracker:
    """Get or create the global job tracker instance."""
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:  # Double-check locking
                _tracker = JobTracker()
    return _tracker
