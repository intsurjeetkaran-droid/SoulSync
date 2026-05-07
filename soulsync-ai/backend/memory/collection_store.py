"""
SoulSync AI - Collection Store (MongoDB)
Typed memory collections: experience, achievement, personal_fact, etc.
"""

import asyncio
import logging
import uuid
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger("soulsync.collection_store")


def _run(coro):
    """Run async coroutine safely from both sync and async contexts."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=30)
    except RuntimeError:
        return asyncio.run(coro)


def _db():
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


def save_to_collection(user_id: str, text: str,
                       override_collection: str = None,
                       override_date=None) -> dict:
    async def _run_inner():
        from backend.processing.collection_classifier import classify_and_extract
        meta = classify_and_extract(text)
        collection = override_collection or meta.get("collection", "conversation")
        event_date = override_date or meta.get("event_date") or date.today()

        db = _db()
        doc_id = str(uuid.uuid4())
        await db.memory_collections.insert_one({
            "_id"       : doc_id,
            "user_id"   : user_id,
            "collection": collection,
            "content"   : text,
            "event_date": str(event_date),
            "importance": meta.get("importance", 5),
            "summary"   : meta.get("summary", ""),
            "extra"     : meta.get("extra", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        return {"collection": collection, "event_date": str(event_date), "id": doc_id}
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.warning(f"[CollectionStore] save failed: {e}")
        return {"collection": "conversation", "event_date": str(date.today())}


def get_entries_in_month(user_id: str, year: int, month: int,
                         collection: str = None) -> list:
    async def _run_inner():
        db = _db()
        prefix = f"{year}-{str(month).zfill(2)}"
        query = {"user_id": user_id, "event_date": {"$regex": f"^{prefix}"}}
        if collection:
            query["collection"] = collection
        cursor = db.memory_collections.find(query).sort("event_date", 1)
        docs = []
        async for doc in cursor:
            docs.append({
                "id"        : str(doc.get("_id", "")),
                "collection": doc.get("collection"),
                "content"   : doc.get("content"),
                "event_date": doc.get("event_date"),
                "importance": doc.get("importance", 5),
                "summary"   : doc.get("summary", ""),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_all_collections_summary(user_id: str) -> dict:
    async def _run_inner():
        db = _db()
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$collection", "count": {"$sum": 1}}},
        ]
        result = {}
        async for doc in db.memory_collections.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result
    try:
        return _run(_run_inner())
    except Exception:
        return {}


def get_earliest_in_collection(user_id: str, collection: str) -> dict | None:
    """Get the oldest entry in a specific collection."""
    async def _run_inner():
        db = _db()
        doc = await db.memory_collections.find_one(
            {"user_id": user_id, "collection": collection},
            sort=[("event_date", 1), ("created_at", 1)]
        )
        if not doc:
            return None
        return {
            "id"        : str(doc.get("_id", "")),
            "collection": doc.get("collection"),
            "content"   : doc.get("content"),
            "event_date": doc.get("event_date"),
            "importance": doc.get("importance", 5),
            "summary"   : doc.get("summary", ""),
            "created_at": str(doc.get("created_at", "")),
        }
    try:
        return _run(_run_inner())
    except Exception:
        return None


def query_collection(user_id: str, collection: str, limit: int = 5,
                     order: str = "DESC") -> list:
    """Query entries from a specific collection."""
    async def _run_inner():
        db = _db()
        sort_dir = -1 if order == "DESC" else 1
        cursor = (
            db.memory_collections
            .find({"user_id": user_id, "collection": collection})
            .sort("event_date", sort_dir)
            .limit(limit)
        )
        docs = []
        async for doc in cursor:
            docs.append({
                "id"        : str(doc.get("_id", "")),
                "collection": doc.get("collection"),
                "content"   : doc.get("content"),
                "event_date": doc.get("event_date"),
                "importance": doc.get("importance", 5),
                "summary"   : doc.get("summary", ""),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def keyword_search_collection(user_id: str, keyword: str,
                               collection: str = None, limit: int = 5) -> list:
    """Search collection entries by keyword."""
    import re as _re
    async def _run_inner():
        db = _db()
        pattern = _re.compile(_re.escape(keyword), _re.IGNORECASE)
        query = {"user_id": user_id, "content": {"$regex": pattern}}
        if collection:
            query["collection"] = collection
        cursor = db.memory_collections.find(query).sort("event_date", -1).limit(limit)
        docs = []
        async for doc in cursor:
            docs.append({
                "id"        : str(doc.get("_id", "")),
                "collection": doc.get("collection"),
                "content"   : doc.get("content"),
                "event_date": doc.get("event_date"),
                "importance": doc.get("importance", 5),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_conversation_chain(user_id: str, entry_id: str, window: int = 3) -> list:
    """Get surrounding entries for context around a specific entry."""
    async def _run_inner():
        db = _db()
        # Get the target entry
        from bson import ObjectId
        try:
            doc = await db.memory_collections.find_one({"_id": ObjectId(entry_id)})
        except Exception:
            doc = await db.memory_collections.find_one({"user_id": user_id})
        if not doc:
            return []
        event_date = doc.get("event_date") or str(doc.get("created_at", ""))
        # Get nearby entries
        cursor = (
            db.memory_collections
            .find({"user_id": user_id})
            .sort("event_date", 1)
            .limit(window * 2 + 1)
        )
        docs = []
        async for d in cursor:
            docs.append({
                "collection": d.get("collection"),
                "content"   : d.get("content"),
                "event_date": d.get("event_date"),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []
