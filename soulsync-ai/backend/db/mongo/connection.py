"""
SoulSync AI - MongoDB Connection (Motor async)
Provides async client lifecycle and index initialization.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from ..config import settings

logger = logging.getLogger("soulsync.db.mongo")

# Module-level client (singleton)
_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Return (or create) the singleton Motor client."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=5,
        )
        logger.info(f"[MongoDB] Client created → {settings.MONGODB_URL}")
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Return the SoulSync MongoDB database handle."""
    return get_mongo_client()[settings.MONGODB_DB]


async def close_mongo_connection() -> None:
    """Close the Motor client on app shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("[MongoDB] Connection closed")


async def init_mongo_indexes() -> None:
    """
    Create all required indexes on startup.
    Safe to call multiple times — MongoDB ignores existing indexes.
    """
    db = get_mongo_db()
    logger.info("[MongoDB] Initializing indexes...")

    try:
        # ── users ──────────────────────────────────────────
        await db.users.create_indexes([
            IndexModel([("user_id", ASCENDING)], unique=True, name="idx_users_user_id"),
            IndexModel([("email", ASCENDING)], unique=True, name="idx_users_email"),
            IndexModel([("created_at", DESCENDING)], name="idx_users_created_at"),
        ])

        # ── conversations ──────────────────────────────────
        await db.conversations.create_indexes([
            IndexModel([("conversation_id", ASCENDING)], unique=True, name="idx_conv_id"),
            IndexModel([("user_id", ASCENDING)], name="idx_conv_user_id"),
            IndexModel([("user_id", ASCENDING), ("last_message_at", DESCENDING)],
                       name="idx_conv_user_last_msg"),
        ])

        # ── messages ───────────────────────────────────────
        await db.messages.create_indexes([
            IndexModel([("message_id", ASCENDING)], unique=True, name="idx_msg_id"),
            IndexModel([("conversation_id", ASCENDING)], name="idx_msg_conv_id"),
            IndexModel([("user_id", ASCENDING)], name="idx_msg_user_id"),
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)],
                       name="idx_msg_user_created"),
            IndexModel([("content", "text")], name="idx_msg_text_search"),
        ])

        # ── memories (personal facts) ──────────────────────
        await db.memories.create_indexes([
            IndexModel([("memory_id", ASCENDING)], unique=True, name="idx_mem_id"),
            IndexModel([("user_id", ASCENDING)], name="idx_mem_user_id"),
            IndexModel([("user_id", ASCENDING), ("key", ASCENDING)],
                       name="idx_mem_user_key"),
            IndexModel([("user_id", ASCENDING), ("context", ASCENDING)],
                       name="idx_mem_user_context"),
        ])

        # ── tasks ──────────────────────────────────────────
        await db.tasks.create_indexes([
            IndexModel([("task_id", ASCENDING)], unique=True, name="idx_task_id"),
            IndexModel([("user_id", ASCENDING)], name="idx_task_user_id"),
            IndexModel([("user_id", ASCENDING), ("status", ASCENDING)],
                       name="idx_task_user_status"),
        ])

        # ── activities ─────────────────────────────────────
        await db.activities.create_indexes([
            IndexModel([("activity_id", ASCENDING)], unique=True, name="idx_act_id"),
            IndexModel([("user_id", ASCENDING)], name="idx_act_user_id"),
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)],
                       name="idx_act_user_created"),
        ])

        # ── mood_logs ──────────────────────────────────────
        await db.mood_logs.create_indexes([
            IndexModel([("log_id", ASCENDING)], unique=True, name="idx_mood_id"),
            IndexModel([("user_id", ASCENDING)], name="idx_mood_user_id"),
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)],
                       name="idx_mood_user_created"),
        ])

        logger.info("[MongoDB] All indexes initialized ✅")

    except Exception as e:
        logger.error(f"[MongoDB] Index initialization failed: {e}", exc_info=True)
        raise
