"""Rate limit and cooldown manager for API services."""

from datetime import datetime, timedelta
from typing import Optional, Dict
from threading import Lock

from logger import logger


class RateLimitStatus:
    """Status information for an API service."""

    def __init__(self, service_name: str, cooldown_seconds: int = 60):
        self.service_name = service_name
        self.cooldown_seconds = cooldown_seconds
        self.cooldown_until: Optional[datetime] = None
        self.message: Optional[str] = None
        self._lock = Lock()

    def is_available(self) -> bool:
        """Check if the service is available (not in cooldown)."""
        with self._lock:
            if self.cooldown_until is None:
                return True

            if datetime.now() >= self.cooldown_until:
                # Cooldown expired, clear it
                self.clear_cooldown()
                return True

            return False

    def enter_cooldown(self, message: str, cooldown_seconds: Optional[int] = None):
        """Put the service into cooldown mode."""
        with self._lock:
            duration = cooldown_seconds or self.cooldown_seconds
            self.cooldown_until = datetime.now() + timedelta(seconds=duration)
            self.message = message

            logger.warning(
                f"{self.service_name} entering cooldown for {duration}s: {message}"
            )

    def clear_cooldown(self):
        """Clear cooldown status."""
        with self._lock:
            if self.cooldown_until is not None:
                logger.info(f"{self.service_name} cooldown cleared")

            self.cooldown_until = None
            self.message = None

    def get_status(self) -> Dict:
        """Get current status as a dictionary."""
        with self._lock:
            available = self.is_available()

            return {
                "available": available,
                "cooldown_until": (
                    self.cooldown_until.isoformat() if self.cooldown_until else None
                ),
                "message": self.message if not available else None
            }

    def get_remaining_cooldown(self) -> Optional[int]:
        """Get remaining cooldown time in seconds."""
        with self._lock:
            if self.cooldown_until is None:
                return None

            remaining = (self.cooldown_until - datetime.now()).total_seconds()
            return max(0, int(remaining))


class RateLimitManager:
    """Global manager for API rate limits and cooldowns."""

    def __init__(self):
        # Initialize rate limit trackers for each service
        self.gemini = RateLimitStatus("Gemini", cooldown_seconds=60)
        self.alpha_vantage = RateLimitStatus("Alpha Vantage", cooldown_seconds=60)

    def get_all_status(self) -> Dict:
        """Get status of all services."""
        return {
            "gemini": self.gemini.get_status(),
            "alpha_vantage": self.alpha_vantage.get_status()
        }


# Global rate limit manager instance
_rate_limit_manager: Optional[RateLimitManager] = None
_manager_lock = Lock()


def get_rate_limit_manager() -> RateLimitManager:
    """Get or create the global rate limit manager."""
    global _rate_limit_manager

    with _manager_lock:
        if _rate_limit_manager is None:
            _rate_limit_manager = RateLimitManager()
            logger.debug("Rate limit manager initialized")

        return _rate_limit_manager
