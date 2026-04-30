"""
SoulSync AI - Redis Cache Manager
Async Redis client using the redis[hiredis] library.
Handles chat response caching, session management, and user cache invalidation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from ..config import settings

logger = logging.getLogger("soulsync.db.redis")

# Module-level client (singleton)
_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Return (or create) the singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            max_connections=20,
        )
        logger.info(f"[Redis] Client created → {settings.REDIS_URL}")
    return _redis_client


async def close_redis_connection() -> None:
    """Close the Redis client on app shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("[Redis] Connection closed")


# ─── Cache Key Helpers ────────────────────────────────────

def chat_cache_key(user_id: str, message: str) -> str:
    """
    Generate a deterministic cache key for a chat response.
    Format: chat:{user_id}:{md5_hash_of_message}
    """
    msg_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()[:16]
    return f"chat:{user_id}:{msg_hash}"


def session_key(user_id: str) -> str:
    """Cache key for user session data. Format: session:{user_id}"""
    return f"session:{user_id}"


def recent_chats_key(user_id: str) -> str:
    """Cache key for recent conversations list. Format: recent_chats:{user_id}"""
    return f"recent_chats:{user_id}"


def facts_cache_key(user_id: str) -> str:
    """Cache key for formatted memory facts. Format: facts:{user_id}"""
    return f"facts:{user_id}"


def user_prefix(user_id: str) -> str:
    """Pattern to match all cache keys for a user."""
    return f"*:{user_id}:*"


# ─── Core Cache Operations ────────────────────────────────

class RedisCacheManager:
    """
    Async Redis cache manager for SoulSync AI.
    All operations are non-blocking and fail gracefully.
    """

    def __init__(self):
        self._client: aioredis.Redis | None = None

    @property
    def client(self) -> aioredis.Redis:
        return get_redis_client()

    async def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return await self.client.ping()
        except Exception as e:
            logger.warning(f"[Redis] Ping failed: {e}")
            return False

    # ── String operations ─────────────────────────────────

    async def get(self, key: str) -> str | None:
        """Get a string value by key. Returns None on miss or error."""
        try:
            value = await self.client.get(key)
            return value
        except Exception as e:
            logger.warning(f"[Redis] get({key}) failed: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set a string value with TTL in seconds. Returns True on success."""
        try:
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"[Redis] set({key}) failed: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"[Redis] delete({key}) failed: {e}")
            return False

    # ── JSON operations ───────────────────────────────────

    async def get_json(self, key: str) -> dict | None:
        """Get a JSON-serialized value. Returns None on miss or error."""
        try:
            raw = await self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"[Redis] get_json({key}) JSON decode error: {e}")
            return None
        except Exception as e:
            logger.warning(f"[Redis] get_json({key}) failed: {e}")
            return None

    async def set_json(self, key: str, data: Any, ttl: int = 300) -> bool:
        """Serialize data to JSON and store with TTL. Returns True on success."""
        try:
            serialized = json.dumps(data, default=str)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"[Redis] set_json({key}) failed: {e}")
            return False

    # ── Chat-specific helpers ─────────────────────────────

    async def cache_chat_response(
        self,
        user_id: str,
        message: str,
        response: str,
        ttl: int = None,
    ) -> bool:
        """
        Cache an AI response for a given user message.
        Uses content-addressed key so identical messages hit the cache.
        """
        ttl = ttl or settings.REDIS_TTL_CHAT
        key = chat_cache_key(user_id, message)
        return await self.set(key, response, ttl=ttl)

    async def get_cached_response(self, user_id: str, message: str) -> str | None:
        """
        Retrieve a cached AI response for a user message.
        Returns None on cache miss.
        """
        key = chat_cache_key(user_id, message)
        return await self.get(key)

    async def cache_recent_conversations(
        self,
        user_id: str,
        conversations: list,
        ttl: int = 300,
    ) -> bool:
        """Cache the recent conversations list for a user."""
        key = recent_chats_key(user_id)
        return await self.set_json(key, conversations, ttl=ttl)

    async def get_recent_conversations(self, user_id: str) -> list | None:
        """Retrieve cached recent conversations. Returns None on miss."""
        key = recent_chats_key(user_id)
        return await self.get_json(key)

    async def cache_facts(self, user_id: str, facts_text: str, ttl: int = 300) -> bool:
        """Cache the formatted memory facts string for a user."""
        key = facts_cache_key(user_id)
        return await self.set(key, facts_text, ttl=ttl)

    async def get_cached_facts(self, user_id: str) -> str | None:
        """Retrieve cached memory facts. Returns None on miss."""
        key = facts_cache_key(user_id)
        return await self.get(key)

    # ── Session helpers ───────────────────────────────────

    async def set_session(self, user_id: str, session_data: dict) -> bool:
        """Store user session data with long TTL."""
        key = session_key(user_id)
        return await self.set_json(key, session_data, ttl=settings.REDIS_TTL_SESSION)

    async def get_session(self, user_id: str) -> dict | None:
        """Retrieve user session data."""
        key = session_key(user_id)
        return await self.get_json(key)

    async def delete_session(self, user_id: str) -> bool:
        """Delete user session (logout)."""
        key = session_key(user_id)
        return await self.delete(key)

    # ── Cache invalidation ────────────────────────────────

    async def invalidate_user_cache(self, user_id: str) -> int:
        """
        Clear all cache keys associated with a user.
        Scans for keys matching patterns: chat:{user_id}:*, session:{user_id},
        recent_chats:{user_id}, facts:{user_id}
        Returns the number of keys deleted.
        """
        try:
            patterns = [
                f"chat:{user_id}:*",
                f"session:{user_id}",
                f"recent_chats:{user_id}",
                f"facts:{user_id}",
            ]
            deleted = 0
            for pattern in patterns:
                # Use SCAN to avoid blocking Redis with KEYS
                async for key in self.client.scan_iter(match=pattern, count=100):
                    await self.client.delete(key)
                    deleted += 1
            logger.info(f"[Redis] Invalidated {deleted} keys for user={user_id}")
            return deleted
        except Exception as e:
            logger.warning(f"[Redis] invalidate_user_cache failed: {e}")
            return 0

    async def invalidate_facts_cache(self, user_id: str) -> bool:
        """Invalidate only the facts cache for a user (after memory update)."""
        key = facts_cache_key(user_id)
        return await self.delete(key)

    # ── TTL helpers ───────────────────────────────────────

    async def ttl(self, key: str) -> int:
        """Return remaining TTL in seconds. -1 = no expiry, -2 = not found."""
        try:
            return await self.client.ttl(key)
        except Exception:
            return -2

    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """Extend the TTL of an existing key."""
        try:
            return await self.client.expire(key, ttl)
        except Exception:
            return False
