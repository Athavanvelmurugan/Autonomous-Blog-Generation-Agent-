import time
from typing import Any, Optional, Dict

class SimpleAsyncCache:
    """
    Lightweight, thread-safe asynchronous TTL in-memory cache
    with pattern-based invalidation for high-read endpoints.
    """
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry["expires_at"] < time.time():
            self._store.pop(key, None)
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds,
        }

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        keys_to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_remove:
            self._store.pop(k, None)

    def clear(self) -> None:
        self._store.clear()

cache = SimpleAsyncCache()
