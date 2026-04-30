"""
SoulSync AI - Life Timeline (MongoDB)
"""

import asyncio
import logging
import uuid
from datetime import datetime, date, timedelta
from typing import Optional

logger = logging.getLogger("soulsync.life_timeline")


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


def add_to_timeline(user_id: str, content: str,
                    collection_type: str = "conversation",
                    event_date=None, source: str = "chat",
                    significance: int = 5, mood: str = None):
    async def _run_inner():
        db = _db()
        ed = event_date or date.today()
        await db.life_timeline.insert_one({
            "entry_id"       : str(uuid.uuid4()),
            "user_id"        : user_id,
            "entry_date"     : str(ed),
            "entry_datetime" : datetime.utcnow(),
            "content"        : content,
            "collection_type": collection_type,
            "significance"   : significance,
            "mood_at_time"   : mood or "",
            "source"         : source,
            "tags"           : [],
            "people_involved": [],
            "created_at"     : datetime.utcnow(),
        })
    try:
        _run(_run_inner())
    except Exception as e:
        logger.warning(f"[Timeline] add failed: {e}")


def get_timeline_for_date(user_id: str, target_date: date) -> list:
    async def _run_inner():
        db = _db()
        cursor = db.life_timeline.find(
            {"user_id": user_id, "entry_date": str(target_date)}
        ).sort("entry_datetime", 1)
        docs = []
        async for doc in cursor:
            docs.append({
                "entry_id"       : doc.get("entry_id"),
                "content"        : doc.get("content"),
                "collection_type": doc.get("collection_type"),
                "significance"   : doc.get("significance", 5),
                "entry_date"     : doc.get("entry_date"),
                "source"         : doc.get("source"),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_timeline_range(user_id: str, start: date, end: date,
                       collection_type: str = None,
                       min_significance: int = 1) -> list:
    async def _run_inner():
        db = _db()
        query = {
            "user_id"     : user_id,
            "entry_date"  : {"$gte": str(start), "$lte": str(end)},
            "significance": {"$gte": min_significance},
        }
        if collection_type:
            query["collection_type"] = collection_type
        cursor = db.life_timeline.find(query).sort("entry_date", 1)
        docs = []
        async for doc in cursor:
            docs.append({
                "entry_id"       : doc.get("entry_id"),
                "content"        : doc.get("content"),
                "collection_type": doc.get("collection_type"),
                "significance"   : doc.get("significance", 5),
                "entry_date"     : doc.get("entry_date"),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_most_significant_moments(user_id: str, limit: int = 10,
                                  min_significance: int = 7) -> list:
    async def _run_inner():
        db = _db()
        cursor = (
            db.life_timeline
            .find({"user_id": user_id, "significance": {"$gte": min_significance}})
            .sort("significance", -1)
            .limit(limit)
        )
        docs = []
        async for doc in cursor:
            docs.append({
                "entry_id"       : doc.get("entry_id"),
                "content"        : doc.get("content"),
                "collection_type": doc.get("collection_type"),
                "significance"   : doc.get("significance", 5),
                "entry_date"     : doc.get("entry_date"),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_day_summary(user_id: str, target_date: date) -> str:
    entries = get_timeline_for_date(user_id, target_date)
    if not entries:
        return "No entries for this day."
    return f"{len(entries)} event(s) on {target_date}."


def get_life_story(user_id: str, limit_days: int = 30) -> list:
    end   = date.today()
    start = end - timedelta(days=limit_days)
    entries = get_timeline_range(user_id, start, end)
    by_day = {}
    for e in entries:
        d = e["entry_date"]
        by_day.setdefault(d, []).append(e)
    return [{"date": d, "events": evts} for d, evts in sorted(by_day.items())]
