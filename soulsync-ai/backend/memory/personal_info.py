"""
SoulSync AI - Personal Info (MongoDB)
Stores and retrieves structured personal facts (name, goal, job, etc.)
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger("soulsync.personal_info")

_APPENDABLE = {"goal", "dream", "aim", "opinion", "interest"}


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


# ── Store ─────────────────────────────────────────────────

def store_personal_info(user_id: str, key: str, value: str,
                        source_text: str = None, event_date=None):
    async def _run_inner():
        import uuid, time
        db = _db()
        key_lower = key.lower()
        now = datetime.utcnow()

        if key_lower in _APPENDABLE:
            unique_key = f"{key_lower}_{int(time.time() * 1000) % 1_000_000}"
            await db.memories.insert_one({
                "memory_id"  : str(uuid.uuid4()),
                "user_id"    : user_id,
                "key"        : unique_key,
                "value"      : value,
                "context"    : "goal",
                "source_text": source_text,
                "event_date" : str(event_date) if event_date else None,
                "created_at" : now,
                "updated_at" : now,
            })
        else:
            await db.memories.find_one_and_update(
                {"user_id": user_id, "key": key_lower},
                {"$set": {
                    "value"      : value,
                    "source_text": source_text,
                    "event_date" : str(event_date) if event_date else None,
                    "updated_at" : now,
                }, "$setOnInsert": {
                    "memory_id" : str(uuid.uuid4()),
                    "user_id"   : user_id,
                    "key"       : key_lower,
                    "context"   : "general",
                    "created_at": now,
                }},
                upsert=True,
                return_document=True,
            )
    try:
        _run(_run_inner())
    except Exception as e:
        logger.warning(f"[PersonalInfo] store failed: {e}")


# ── Get all facts ─────────────────────────────────────────

def get_all_facts(user_id: str) -> list:
    async def _run_inner():
        db = _db()
        cursor = db.memories.find({"user_id": user_id}).sort("created_at", -1)
        docs = []
        async for doc in cursor:
            docs.append({
                "key"        : doc.get("key"),
                "value"      : doc.get("value"),
                "context"    : doc.get("context", "general"),
                "source_text": doc.get("source_text"),
                "event_date" : doc.get("event_date"),
                "created_at" : str(doc.get("created_at", "")),
                "updated_at" : str(doc.get("updated_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_fact(user_id: str, key: str) -> Optional[str]:
    async def _run_inner():
        db = _db()
        doc = await db.memories.find_one(
            {"user_id": user_id, "key": key.lower()},
            sort=[("created_at", -1)]
        )
        return doc["value"] if doc else None
    try:
        return _run(_run_inner())
    except Exception:
        return None


def get_goals_timeline(user_id: str) -> list:
    async def _run_inner():
        import re
        db = _db()
        cursor = db.memories.find(
            {"user_id": user_id, "key": {"$regex": re.compile("^goal", re.IGNORECASE)}}
        ).sort("created_at", 1)
        docs = []
        async for doc in cursor:
            docs.append({
                "key"       : doc.get("key"),
                "value"     : doc.get("value"),
                "event_date": doc.get("event_date"),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


def get_facts_in_period(user_id: str, start, end) -> list:
    async def _run_inner():
        db = _db()
        cursor = db.memories.find({
            "user_id"   : user_id,
            "created_at": {"$gte": datetime.combine(start, datetime.min.time()),
                           "$lte": datetime.combine(end,   datetime.max.time())}
        }).sort("created_at", 1)
        docs = []
        async for doc in cursor:
            docs.append({
                "key"       : doc.get("key"),
                "value"     : doc.get("value"),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    try:
        return _run(_run_inner())
    except Exception:
        return []


# ── Format for AI prompt ──────────────────────────────────

def format_for_prompt(user_id: str) -> str:
    facts = get_all_facts(user_id)
    if not facts:
        return ""
    labels = {
        "name": "Name", "age": "Age", "goal": "Goal", "dream": "Dream",
        "aim": "Aim", "job": "Job", "hobby": "Hobby", "interest": "Interest",
        "location": "Location", "email": "Email", "phone": "Phone",
    }
    lines = []
    for f in facts:
        raw_key = f["key"].split("_")[0]
        label = labels.get(raw_key, raw_key.replace("_", " ").title())
        date_str = f" (updated {f['updated_at'][:10]})" if f.get("updated_at") else ""
        lines.append(f"- {label}: {f['value']}{date_str}")
    return "Known facts about this user:\n" + "\n".join(lines)


# ── Build direct answer ───────────────────────────────────

def build_direct_answer(user_id: str, query_key: Optional[str]) -> Optional[str]:
    if query_key == "__earliest__":
        from backend.memory.memory_manager import get_earliest_memories
        earliest = get_earliest_memories(user_id, limit=3)
        if not earliest:
            return None
        lines = [f'• [{m["created_at"][:10]}] "{m["message"]}"' for m in earliest]
        return "Here are the earliest things you shared with me:\n" + "\n".join(lines) + "\n\nThese are your first memories in SoulSync. 🧠"

    if query_key is None:
        facts = get_all_facts(user_id)
        if not facts:
            return None
        labels = {"name":"Name","age":"Age","goal":"Goal","dream":"Dream","aim":"Aim",
                  "job":"Job","hobby":"Hobby","interest":"Interest","location":"Location"}
        lines = []
        for f in facts:
            raw_key = f["key"].split("_")[0]
            label = labels.get(raw_key, raw_key.replace("_"," ").title())
            lines.append(f"• {label}: {f['value']}")
        return "Here's what I know about you:\n" + "\n".join(lines) + " 😊"

    if query_key == "goal":
        goals = get_goals_timeline(user_id)
        if not goals:
            return None
        if len(goals) == 1:
            g = goals[0]
            return f"Your goal is: {g['value']} 💪"
        lines = [f"• [{g.get('event_date') or g['created_at'][:10]}] {g['value']}" for g in goals]
        return "Your goals over time:\n" + "\n".join(lines) + " 💪"

    value = get_fact(user_id, query_key)
    if not value:
        return None

    answers = {
        "name"    : f"Your name is {value} 😊",
        "age"     : f"You are {value} years old.",
        "goal"    : f"Your goal is: {value} 💪",
        "dream"   : f"Your dream is: {value} ✨",
        "aim"     : f"Your aim is: {value}",
        "job"     : f"You work as: {value}",
        "hobby"   : f"Your hobby is: {value}",
        "interest": f"You enjoy: {value}",
        "location": f"You live in {value}.",
        "email"   : f"Your email is {value}.",
        "phone"   : f"Your phone number is {value}.",
    }
    return answers.get(query_key, f"Your {query_key.replace('_',' ')} is: {value}")
