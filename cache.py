"""File-based caching for API responses."""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional

from logger import logger


class APICache:
    """File-based cache for API responses with TTL support."""

    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 24):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (0 = never expire)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours) if ttl_hours > 0 else None

    def _get_cache_key(self, *args) -> str:
        """Generate a unique cache key from arguments."""
        key_str = "_".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_file(self, key: str) -> Path:
        """Get the cache file path for a key."""
        return self.cache_dir / f"{key}.json"

    def get(self, *args) -> Optional[Any]:
        """
        Get cached data if it exists and hasn't expired.

        Args:
            *args: Arguments used to generate the cache key

        Returns:
            Cached data or None if not found/expired
        """
        key = self._get_cache_key(*args)
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return None

        # Check TTL
        if self.ttl:
            file_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            if file_age > self.ttl:
                logger.debug(f"Cache expired for key {key[:8]}...")
                cache_file.unlink()
                return None

        try:
            data = json.loads(cache_file.read_text())
            logger.debug(f"Cache hit for key {key[:8]}...")
            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def set(self, data: Any, *args) -> bool:
        """
        Save data to cache.

        Args:
            data: Data to cache (must be JSON serializable)
            *args: Arguments used to generate the cache key

        Returns:
            True if successful, False otherwise
        """
        key = self._get_cache_key(*args)
        cache_file = self._get_cache_file(key)

        try:
            cache_file.write_text(json.dumps(data, default=str, indent=2))
            logger.debug(f"Cached data with key {key[:8]}...")
            return True
        except (TypeError, IOError) as e:
            logger.warning(f"Failed to write cache: {e}")
            return False

    def invalidate(self, *args) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            *args: Arguments used to generate the cache key

        Returns:
            True if entry was removed, False if not found
        """
        key = self._get_cache_key(*args)
        cache_file = self._get_cache_file(key)

        if cache_file.exists():
            cache_file.unlink()
            logger.debug(f"Invalidated cache key {key[:8]}...")
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cache files.

        Returns:
            Number of files removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        logger.info(f"Cleared {count} cache entries")
        return count

    def get_stats(self) -> dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "entries": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl.total_seconds() / 3600 if self.ttl else None
        }


# Pre-configured cache instances
news_cache = APICache(cache_dir=".cache/news", ttl_hours=24)
analysis_cache = APICache(cache_dir=".cache/analysis", ttl_hours=168)  # 1 week
