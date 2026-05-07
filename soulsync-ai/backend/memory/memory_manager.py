"""
SoulSync AI - Memory Manager (MongoDB)
All memory operations backed by MongoDB (Motor async).
Sync wrappers provided so existing callers work without changes.
"""

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger("soulsync.memory_manager")


# ── Async helper ──────────────────────────────────────────

def _run(coro):
    """Run async coroutine safely from both sync and async contexts."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # We're inside a running event loop (FastAPI) — use a thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=30)
    except RuntimeError:
        # No running loop — run directly
        return asyncio.run(coro)


def _db():
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


# ── Ensure user exists ────────────────────────────────────

def ensure_user_exists(user_id: str, name: str = None):
    async def _run_inner():
        db = _db()
        existing = await db.users.find_one({"user_id": user_id})
        if not existing:
            await db.users.insert_one({
                "user_id"   : user_id,
                "name"      : name or user_id,
                "email"     : f"{user_id}@legacy.soulsync.ai",
                "password_hash": "",
                "profile"   : {},
                "preferences": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
    try:
        _run(_run_inner())
    except Exception as e:
        logger.warning(f"[MemMgr] ensure_user_exists failed: {e}")


# ── Save memory ───────────────────────────────────────────

def save_memory(user_id: str, role: str, message: str, importance_score: int = None):
    if importance_score is None:
        try:
            from backend.processing.scorer import score_memory
            importance_score = score_memory(message, user_id, role).get("score", 5)
        except Exception:
            importance_score = 5

    async def _run_inner():
        import uuid
        db = _db()
        await db.messages.insert_one({
            "message_id"      : str(uuid.uuid4()),
            "conversation_id" : f"legacy_{user_id}",
            "user_id"         : user_id,
            "role"            : role,
            "content"         : message,
            "importance_score": importance_score,
            "emotion"         : "neutral",
            "intent"          : "normal_chat",
            "created_at"      : datetime.utcnow(),
        })
    try:
        _run(_run_inner())
    except Exception as e:
        logger.warning(f"[MemMgr] save_memory failed: {e}")


def save_conversation(user_id: str, user_message: str, ai_response: str):
    ensure_user_exists(user_id)
    save_memory(user_id, "user",      user_message)
    save_memory(user_id, "assistant", ai_response)


# ── Fetch memories ────────────────────────────────────────

def get_memories(user_id: str, limit: int = 20) -> list:
    async def _run_inner():
        db = _db()
        cursor = db.messages.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        docs = []
        async for doc in cursor:
            docs.append({
                "id"              : str(doc.get("_id", "")),
                "user_id"         : doc.get("user_id"),
                "role"            : doc.get("role"),
                "message"         : doc.get("content", ""),
                "importance_score": doc.get("importance_score", 5),
                "created_at"      : str(doc.get("created_at", "")),
            })
        return list(reversed(docs))
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.warning(f"[MemMgr] get_memories failed: {e}")
        return []


def get_earliest_memories(user_id: str, limit: int = 5) -> list:
    async def _run_inner():
        db = _db()
        cursor = (
            db.messages
            .find({"user_id": user_id, "role": "user"})
            .sort("created_at", 1)
            .limit(limit)
        )
        docs = []
        async for doc in cursor:
            docs.append({
                "id"        : str(doc.get("_id", "")),
                "role"      : doc.get("role"),
                "message"   : doc.get("content", ""),
                "importance_score": doc.get("importance_score", 5),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.warning(f"[MemMgr] get_earliest_memories failed: {e}")
        return []


def search_memories_by_keyword(user_id: str, keyword: str, limit: int = 5) -> list:
    async def _run_inner():
        import re
        db = _db()
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        cursor = (
            db.messages
            .find({"user_id": user_id, "role": "user", "content": {"$regex": pattern}})
            .sort("created_at", 1)
            .limit(limit)
        )
        docs = []
        async for doc in cursor:
            docs.append({
                "id"        : str(doc.get("_id", "")),
                "role"      : doc.get("role"),
                "message"   : doc.get("content", ""),
                "importance_score": doc.get("importance_score", 5),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.warning(f"[MemMgr] search_memories_by_keyword failed: {e}")
        return []


def get_chat_history(user_id: str, turns: int = 5) -> list:
    memories = get_memories(user_id, limit=turns * 2)
    history = []
    i = 0
    while i < len(memories) - 1:
        if memories[i]["role"] == "user" and memories[i+1]["role"] == "assistant":
            history.append((memories[i]["message"], memories[i+1]["message"]))
            i += 2
        else:
            i += 1
    return history[-turns:]


def get_memory_count(user_id: str) -> int:
    async def _run_inner():
        db = _db()
        return await db.messages.count_documents({"user_id": user_id})
    try:
        return _run(_run_inner())
    except Exception:
        return 0
