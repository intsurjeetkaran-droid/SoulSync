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
