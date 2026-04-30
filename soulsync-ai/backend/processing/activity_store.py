"""
SoulSync AI - Activity Store (MongoDB)
"""

import asyncio
import logging
import uuid
from datetime import datetime

logger = logging.getLogger("soulsync.activity_store")


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _db():
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


def save_activity(user_id: str, raw_text: str, extracted: dict) -> str:
    async def _run_inner():
        db = _db()
        activity_id = str(uuid.uuid4())
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id"    : user_id,
            "raw_text"   : raw_text,
            "emotion"    : extracted.get("emotion", "neutral") or "neutral",
            "activity"   : extracted.get("activity", "") or "",
            "status"     : extracted.get("status", "") or "",
            "productivity": extracted.get("productivity", "") or "",
            "summary"    : extracted.get("summary", "") or "",
            "created_at" : datetime.utcnow(),
        })
        return activity_id
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.warning(f"[ActivityStore] save failed: {e}")
        return ""


def get_activities(user_id: str, limit: int = 20) -> list:
    async def _run_inner():
        db = _db()
        cursor = db.activities.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        docs = []
        async for doc in cursor:
            docs.append({
                "activity_id": doc.get("activity_id"),
                "user_id"    : doc.get("user_id"),
                "raw_text"   : doc.get("raw_text", ""),
                "emotion"    : doc.get("emotion", "neutral"),
                "activity"   : doc.get("activity", ""),
                "status"     : doc.get("status", ""),
                "productivity": doc.get("productivity", ""),
                "summary"    : doc.get("summary", ""),
                "created_at" : str(doc.get("created_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_emotion_summary(user_id: str) -> dict:
    async def _run_inner():
        db = _db()
        pipeline = [
            {"$match": {"user_id": user_id, "emotion": {"$ne": ""}}},
            {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = {}
        async for doc in db.activities.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result
    try:
        return _run(_run_inner())
    except Exception:
        return {}
