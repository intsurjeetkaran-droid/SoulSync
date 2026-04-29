"""
SoulSync AI - Response Cache
In-memory LRU cache for AI responses.

Avoids re-computing identical or very similar queries.
Uses hashlib for cache keys.

Cache strategy:
  - Key   : hash of (user_id + message)
  - Value : AI response string
  - TTL   : 10 minutes
  - Size  : max 200 entries
"""

import hashlib
import time
from collections import OrderedDict
from threading import Lock

# ─── Config ───────────────────────────────────────────────
MAX_SIZE  = 200          # max cached entries
TTL_SECS  = 600          # 10 minutes


class LRUCache:
    """
    Thread-safe LRU cache with TTL expiry.
    """

    def __init__(self, max_size: int = MAX_SIZE, ttl: int = TTL_SECS):
        self._cache    : OrderedDict = OrderedDict()
        self._max_size : int         = max_size
        self._ttl      : int         = ttl
        self._lock     : Lock        = Lock()
        self._hits     : int         = 0
        self._misses   : int         = 0

    def _make_key(self, user_id: str, message: str) -> str:
        """Create a deterministic cache key."""
        raw = f"{user_id}::{message.strip().lower()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, user_id: str, message: str):
        """
        Retrieve cached response.
        Returns None if not found or expired.
        """
        key = self._make_key(user_id, message)

        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp = self._cache[key]

            # Check TTL
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, user_id: str, message: str, response: str):
        """Store a response in the cache."""
        key = self._make_key(user_id, message)

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (response, time.time())

            # Evict oldest if over max size
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._hits + self._misses
        rate  = (self._hits / total * 100) if total > 0 else 0
        return {
            "size"     : len(self._cache),
            "max_size" : self._max_size,
            "hits"     : self._hits,
            "misses"   : self._misses,
            "hit_rate" : f"{rate:.1f}%",
            "ttl_secs" : self._ttl,
        }


# ─── Global Cache Instance ────────────────────────────────
response_cache = LRUCache()
