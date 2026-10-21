import time
import logging
from typing import Optional, Any, Dict
from backend.app.config import get_settings

logger = logging.getLogger(__name__)


class SearchCache:
    """
    In-memory TTL cache for search queries and scraped web documents.
    Prevents redundant external API calls within SEARCH_CACHE_TTL_HOURS window.
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_key(self, query: str) -> str:
        return query.strip().lower()

    def get(self, query: str) -> Optional[Any]:
        settings = get_settings()
        ttl_seconds = settings.SEARCH_CACHE_TTL_HOURS * 3600
        key = self._normalize_key(query)
        entry = self._cache.get(key)
        if not entry:
            return None
        
        if (time.time() - entry["timestamp"]) > ttl_seconds:
            logger.debug(f"[SearchCache] TTL expired for query: '{query}'")
            del self._cache[key]
            return None
        
        logger.info(f"[SearchCache] Cache hit for query: '{query}'")
        return entry["data"]

    def set(self, query: str, data: Any) -> None:
        key = self._normalize_key(query)
        self._cache[key] = {
            "timestamp": time.time(),
            "data": data,
        }

    def clear(self) -> None:
        self._cache.clear()


# Global singleton instance
search_cache = SearchCache()
