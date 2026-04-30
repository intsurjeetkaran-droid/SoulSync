"""
SoulSync AI - Task Manager (MongoDB)
All task CRUD backed by MongoDB.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from backend.tasks.task_detector import detect_tasks

logger = logging.getLogger("soulsync.task_manager")


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


def _serialize(doc: dict) -> dict:
    if not doc:
        return {}
    return {
        "id"        : doc.get("task_id", str(doc.get("_id", ""))),
        "task_id"   : doc.get("task_id", ""),
        "user_id"   : doc.get("user_id"),
        "title"     : doc.get("title"),
        "due_date"  : doc.get("due_date"),
        "priority"  : doc.get("priority", "medium"),
        "status"    : doc.get("status", "pending"),
        "source"    : doc.get("source", "manual"),
        "created_at": str(doc.get("created_at", "")),
    }


# ── Create ────────────────────────────────────────────────

def create_task(user_id: str, title: str, due_date: str = None,
                priority: str = "medium", source: str = "manual") -> dict:
    async def _run_inner():
        db = _db()
        task_id = str(uuid.uuid4())
        doc = {
            "task_id"   : task_id,
            "user_id"   : user_id,
            "title"     : title,
            "due_date"  : due_date,
            "priority"  : priority,
            "status"    : "pending",
            "source"    : source,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await db.tasks.insert_one(doc)
        return _serialize(doc)
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] create_task failed: {e}")
        raise


# ── Get ───────────────────────────────────────────────────

def get_tasks(user_id: str, status: str = None) -> list:
    async def _run_inner():
        db = _db()
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        cursor = db.tasks.find(query).sort("created_at", -1)
        docs = [_serialize(doc) async for doc in cursor]
        priority_order = {"high": 1, "medium": 2, "low": 3}
        docs.sort(key=lambda d: priority_order.get(d.get("priority", "medium"), 2))
        return docs
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] get_tasks failed: {e}")
        return []


# ── Complete ──────────────────────────────────────────────

def complete_task(task_id, user_id: str) -> dict:
    """task_id can be int (legacy) or str (MongoDB task_id)."""
    async def _run_inner():
        db = _db()
        task_id_str = str(task_id)
        result = await db.tasks.find_one_and_update(
            {"$or": [{"task_id": task_id_str}, {"task_id": task_id}], "user_id": user_id},
            {"$set": {"status": "completed", "completed_at": datetime.utcnow(),
                      "updated_at": datetime.utcnow()}},
            return_document=True,
        )
        return _serialize(result) if result else {}
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] complete_task failed: {e}")
        return {}


# ── Delete ────────────────────────────────────────────────

def delete_task(task_id, user_id: str) -> bool:
    async def _run_inner():
        db = _db()
        task_id_str = str(task_id)
        result = await db.tasks.delete_one(
            {"$or": [{"task_id": task_id_str}, {"task_id": task_id}], "user_id": user_id}
        )
        return result.deleted_count > 0
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] delete_task failed: {e}")
        return False


# ── Auto-create from chat ─────────────────────────────────

def auto_create_tasks(user_id: str, message: str) -> list:
    detected = detect_tasks(message)
    created = []
    for task_data in detected:
        task = create_task(
            user_id  = user_id,
            title    = task_data["title"],
            due_date = task_data.get("due_date"),
            priority = task_data.get("priority", "medium"),
            source   = "auto",
        )
        created.append(task)
    return created


# ── Summary ───────────────────────────────────────────────

def get_task_summary(user_id: str) -> dict:
    all_tasks = get_tasks(user_id)
    pending   = [t for t in all_tasks if t["status"] == "pending"]
    completed = [t for t in all_tasks if t["status"] == "completed"]
    high_pri  = [t for t in pending   if t["priority"] == "high"]
    return {
        "total"                : len(all_tasks),
        "pending"              : len(pending),
        "completed"            : len(completed),
        "high_priority_pending": len(high_pri),
    }
