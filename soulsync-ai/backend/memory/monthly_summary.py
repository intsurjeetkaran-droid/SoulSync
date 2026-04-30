"""
SoulSync AI - Monthly Summary (MongoDB)
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("soulsync.monthly_summary")


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


def build_monthly_summary(user_id: str, year: int, month: int) -> dict:
    async def _run_inner():
        from backend.memory.collection_store import get_entries_in_month
        entries = get_entries_in_month(user_id, year, month)

        experiences  = [e["content"] for e in entries if e.get("collection") == "experience"]
        achievements = [e["content"] for e in entries if e.get("collection") == "achievement"]

        db = _db()
        prefix = f"{year}-{str(month).zfill(2)}"
        pipeline = [
            {"$match": {"user_id": user_id, "created_at": {
                "$gte": datetime(year, month, 1),
                "$lt" : datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1),
            }}},
            {"$group": {"_id": "$mood", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        mood_counts = {}
        async for doc in db.mood_logs.aggregate(pipeline):
            mood_counts[doc["_id"]] = doc["count"]

        dominant_mood = max(mood_counts, key=mood_counts.get) if mood_counts else "neutral"

        summary = {
            "year_month"    : f"{year}-{str(month).zfill(2)}",
            "experiences"   : experiences[:10],
            "achievements"  : achievements[:10],
            "dominant_mood" : dominant_mood,
            "mood_counts"   : mood_counts,
            "total_entries" : len(entries),
        }

        # Upsert into monthly_summaries collection
        await db.monthly_summaries.find_one_and_update(
            {"user_id": user_id, "year_month": summary["year_month"]},
            {"$set": {**summary, "user_id": user_id, "updated_at": datetime.utcnow()}},
            upsert=True,
        )
        return summary
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.warning(f"[MonthlySummary] build failed: {e}")
        return {}
