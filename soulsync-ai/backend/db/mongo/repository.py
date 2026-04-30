"""
SoulSync AI - MongoDB Repository
Full async CRUD layer using Motor.
All methods return plain dict / list — no ORM objects exposed.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import (
    UserDocument,
    ConversationDocument,
    MessageDocument,
    MemoryDocument,
    TaskDocument,
    ActivityDocument,
    MoodLogDocument,
)

logger = logging.getLogger("soulsync.db.mongo.repo")

# Keys that allow multiple values (append) vs single canonical value (upsert)
_APPENDABLE_KEYS = {"goal", "dream", "aim", "opinion", "interest"}

# Context mapping for memory keys
_KEY_CONTEXT = {
    "name": "identity", "age": "identity", "email": "identity",
    "phone": "identity", "location": "identity",
    "job": "career",
    "goal": "goal", "dream": "goal", "aim": "goal",
    "hobby": "preference", "interest": "preference",
}


def _serialize(doc: dict) -> dict:
    """Convert MongoDB document to JSON-safe dict (remove _id, stringify dates)."""
    result = {}
    for k, v in doc.items():
        if k == "_id":
            continue
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result


class MongoRepository:
    """
    Async repository for all MongoDB collections.
    Instantiate with a Motor database handle.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.conversations = db.conversations
        self.messages = db.messages
        self.memories = db.memories
        self.tasks = db.tasks
        self.activities = db.activities
        self.mood_logs = db.mood_logs

    # ═══════════════════════════════════════════════════════
    # USER OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def create_user(self, user_data: dict) -> dict:
        """
        Create a new user document.
        user_data must include: name, email, password_hash
        Returns the created user dict (without password_hash).
        """
        try:
            doc = UserDocument(**user_data)
            payload = doc.model_dump()
            await self.users.insert_one(payload)
            logger.info(f"[Mongo] User created: {doc.email} → {doc.user_id}")
            return _serialize({k: v for k, v in payload.items() if k != "password_hash"})
        except Exception as e:
            logger.error(f"[Mongo] create_user failed: {e}", exc_info=True)
            raise

    async def get_user_by_email(self, email: str) -> dict | None:
        """Fetch user by email. Returns full doc including password_hash."""
        try:
            doc = await self.users.find_one({"email": email.lower().strip()})
            return _serialize(doc) if doc else None
        except Exception as e:
            logger.error(f"[Mongo] get_user_by_email failed: {e}", exc_info=True)
            return None

    async def get_user_by_id(self, user_id: str) -> dict | None:
        """Fetch user by user_id. Returns doc without password_hash."""
        try:
            doc = await self.users.find_one({"user_id": user_id})
            if not doc:
                return None
            doc.pop("password_hash", None)
            return _serialize(doc)
        except Exception as e:
            logger.error(f"[Mongo] get_user_by_id failed: {e}", exc_info=True)
            return None

    async def get_user_with_password(self, email: str) -> dict | None:
        """Fetch user including password_hash for authentication."""
        try:
            doc = await self.users.find_one({"email": email.lower().strip()})
            if not doc:
                return None
            result = _serialize(doc)
            # Re-add password_hash from raw doc (not serialized away)
            result["password_hash"] = doc.get("password_hash", "")
            return result
        except Exception as e:
            logger.error(f"[Mongo] get_user_with_password failed: {e}", exc_info=True)
            return None

    async def update_user_profile(self, user_id: str, profile: dict) -> bool:
        """
        Merge-update the profile sub-document for a user.
        Returns True if a document was modified.
        """
        try:
            update_fields: dict[str, Any] = {"updated_at": datetime.utcnow()}
            for k, v in profile.items():
                update_fields[f"profile.{k}"] = v
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": update_fields},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"[Mongo] update_user_profile failed: {e}", exc_info=True)
            return False

    # ═══════════════════════════════════════════════════════
    # CONVERSATION OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def create_conversation(self, user_id: str, title: str = "New Conversation") -> dict:
        """Create a new conversation document. Returns the created doc."""
        try:
            doc = ConversationDocument(user_id=user_id, title=title)
            payload = doc.model_dump()
            await self.conversations.insert_one(payload)
            logger.info(f"[Mongo] Conversation created: {doc.conversation_id} for user={user_id}")
            return _serialize(payload)
        except Exception as e:
            logger.error(f"[Mongo] create_conversation failed: {e}", exc_info=True)
            raise

    async def get_conversations(self, user_id: str, limit: int = 20, skip: int = 0) -> list:
        """Fetch paginated conversations for a user, newest first."""
        try:
            cursor = (
                self.conversations
                .find({"user_id": user_id})
                .sort("last_message_at", -1)
                .skip(skip)
                .limit(limit)
            )
            return [_serialize(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"[Mongo] get_conversations failed: {e}", exc_info=True)
            return []

    async def get_conversation(self, conversation_id: str) -> dict | None:
        """Fetch a single conversation by ID."""
        try:
            doc = await self.conversations.find_one({"conversation_id": conversation_id})
            return _serialize(doc) if doc else None
        except Exception as e:
            logger.error(f"[Mongo] get_conversation failed: {e}", exc_info=True)
            return None

    async def update_conversation_meta(self, conversation_id: str, updates: dict) -> bool:
        """Update conversation metadata (title, message_count, last_message_at, etc.)."""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$set": updates},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"[Mongo] update_conversation_meta failed: {e}", exc_info=True)
            return False

    # ═══════════════════════════════════════════════════════
    # MESSAGE OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def save_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        **kwargs,
    ) -> dict:
        """
        Save a single message to the messages collection.
        kwargs: importance_score, emotion, intent
        Returns the saved message dict.
        """
        try:
            doc = MessageDocument(
                user_id=user_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                importance_score=kwargs.get("importance_score", 5),
                emotion=kwargs.get("emotion", "neutral"),
                intent=kwargs.get("intent", "normal_chat"),
            )
            payload = doc.model_dump()
            await self.messages.insert_one(payload)

            # Update conversation metadata
            await self.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$inc": {"message_count": 1},
                    "$set": {
                        "last_message_at": doc.created_at,
                        "updated_at": doc.created_at,
                    },
                },
            )

            logger.debug(f"[Mongo] Message saved: {doc.message_id} role={role}")
            return _serialize(payload)
        except Exception as e:
            logger.error(f"[Mongo] save_message failed: {e}", exc_info=True)
            raise

    async def get_messages(
        self, conversation_id: str, limit: int = 50, skip: int = 0
    ) -> list:
        """Fetch paginated messages for a conversation, oldest first."""
        try:
            cursor = (
                self.messages
                .find({"conversation_id": conversation_id})
                .sort("created_at", 1)
                .skip(skip)
                .limit(limit)
            )
            return [_serialize(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"[Mongo] get_messages failed: {e}", exc_info=True)
            return []

    async def get_recent_messages(self, user_id: str, limit: int = 10) -> list:
        """Fetch the most recent messages across all conversations for a user."""
        try:
            cursor = (
                self.messages
                .find({"user_id": user_id})
                .sort("created_at", -1)
                .limit(limit)
            )
            docs = [_serialize(doc) async for doc in cursor]
            return list(reversed(docs))  # return in chronological order
        except Exception as e:
            logger.error(f"[Mongo] get_recent_messages failed: {e}", exc_info=True)
            return []

    async def get_earliest_messages(self, user_id: str, limit: int = 5) -> list:
        """Fetch the oldest user messages — for 'first memory' queries."""
        try:
            cursor = (
                self.messages
                .find({"user_id": user_id, "role": "user"})
                .sort("created_at", 1)
                .limit(limit)
            )
            return [_serialize(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"[Mongo] get_earliest_messages failed: {e}", exc_info=True)
            return []

    async def search_messages(self, user_id: str, keyword: str, limit: int = 10) -> list:
        """
        Full-text keyword search across messages for a user.
        Uses MongoDB text index if available, falls back to regex.
        """
        try:
            # Try text index first
            try:
                cursor = (
                    self.messages
                    .find(
                        {"$text": {"$search": keyword}, "user_id": user_id},
                        {"score": {"$meta": "textScore"}},
                    )
                    .sort([("score", {"$meta": "textScore"})])
                    .limit(limit)
                )
                results = [_serialize(doc) async for doc in cursor]
                if results:
                    return results
            except Exception:
                pass

            # Fallback: regex search
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            cursor = (
                self.messages
                .find({"user_id": user_id, "content": {"$regex": pattern}})
                .sort("created_at", -1)
                .limit(limit)
            )
            return [_serialize(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"[Mongo] search_messages failed: {e}", exc_info=True)
            return []

    async def get_chat_history_turns(self, user_id: str, conversation_id: str, turns: int = 5) -> list:
        """
        Return last N conversation turns as list of (user_msg, assistant_msg) tuples.
        Used to feed context into the AI model.
        """
        try:
            cursor = (
                self.messages
                .find({"conversation_id": conversation_id, "user_id": user_id})
                .sort("created_at", -1)
                .limit(turns * 2)
            )
            docs = list(reversed([doc async for doc in cursor]))
            history = []
            i = 0
            while i < len(docs) - 1:
                if docs[i]["role"] == "user" and docs[i + 1]["role"] == "assistant":
                    history.append((docs[i]["content"], docs[i + 1]["content"]))
                    i += 2
                else:
                    i += 1
            return history[-turns:]
        except Exception as e:
            logger.error(f"[Mongo] get_chat_history_turns failed: {e}", exc_info=True)
            return []

    # ═══════════════════════════════════════════════════════
    # MEMORY / PERSONAL INFO OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def store_memory_fact(
        self,
        user_id: str,
        key: str,
        value: str,
        **kwargs,
    ) -> dict:
        """
        Store a personal fact in the memories collection.
        Appendable keys (goal, dream, etc.) always insert new docs.
        Other keys upsert (replace existing value).
        kwargs: source_text, context, event_date
        """
        try:
            key_lower = key.lower()
            context = kwargs.get("context") or _KEY_CONTEXT.get(key_lower, "general")
            source_text = kwargs.get("source_text")
            event_date = kwargs.get("event_date")

            if key_lower in _APPENDABLE_KEYS:
                # Always append — preserve history
                import time as _time
                unique_key = f"{key_lower}_{int(_time.time() * 1000) % 1_000_000}"
                doc = MemoryDocument(
                    user_id=user_id,
                    key=unique_key,
                    value=value,
                    context=context,
                    source_text=source_text,
                    event_date=event_date,
                )
                payload = doc.model_dump()
                await self.memories.insert_one(payload)
            else:
                # Upsert — single canonical value per key
                now = datetime.utcnow()
                result = await self.memories.find_one_and_update(
                    {"user_id": user_id, "key": key_lower},
                    {
                        "$set": {
                            "value": value,
                            "context": context,
                            "source_text": source_text,
                            "event_date": event_date,
                            "updated_at": now,
                        },
                        "$setOnInsert": {
                            "memory_id": str(__import__("uuid").uuid4()),
                            "user_id": user_id,
                            "key": key_lower,
                            "created_at": now,
                        },
                    },
                    upsert=True,
                    return_document=True,
                )
                payload = result or {}

            logger.info(f"[Mongo] Memory stored: user={user_id} key={key_lower} value={value[:40]}")
            return _serialize(payload)
        except Exception as e:
            logger.error(f"[Mongo] store_memory_fact failed: {e}", exc_info=True)
            raise

    async def get_memory_facts(self, user_id: str, key: str = None) -> list:
        """
        Retrieve memory facts for a user.
        If key is provided, filter by key prefix.
        """
        try:
            query: dict[str, Any] = {"user_id": user_id}
            if key:
                query["key"] = {"$regex": f"^{re.escape(key.lower())}"}
            cursor = (
                self.memories
                .find(query)
                .sort("created_at", -1)
            )
            return [_serialize(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"[Mongo] get_memory_facts failed: {e}", exc_info=True)
            return []

    async def get_single_fact(self, user_id: str, key: str) -> str | None:
        """Return the most recent value for a specific key. None if not found."""
        try:
            doc = await self.memories.find_one(
                {"user_id": user_id, "key": key.lower()},
                sort=[("created_at", -1)],
            )
            return doc["value"] if doc else None
        except Exception as e:
            logger.error(f"[Mongo] get_single_fact failed: {e}", exc_info=True)
            return None

    async def format_facts_for_prompt(self, user_id: str) -> str:
        """
        Format all personal facts as a readable context block for the AI prompt.
        Groups by context category.
        """
        try:
            facts = await self.get_memory_facts(user_id)
            if not facts:
                return ""

            key_labels = {
                "name": "Name", "age": "Age", "goal": "Goal", "dream": "Dream",
                "aim": "Aim", "job": "Job / Profession", "hobby": "Hobby",
                "interest": "Interest", "location": "Location",
                "email": "Email", "phone": "Phone",
            }

            groups: dict[str, list] = {}
            for f in facts:
                ctx = f.get("context") or "general"
                groups.setdefault(ctx, []).append(f)

            lines = []
            ctx_order = ["identity", "career", "goal", "preference", "general"]
            for ctx in ctx_order:
                if ctx not in groups:
                    continue
                for f in groups[ctx]:
                    raw_key = f["key"].split("_")[0]
                    label = key_labels.get(raw_key, raw_key.replace("_", " ").title())
                    date_str = ""
                    if f.get("event_date"):
                        date_str = f" (set {str(f['event_date'])[:10]})"
                    elif f.get("updated_at"):
                        date_str = f" (updated {str(f['updated_at'])[:10]})"
                    lines.append(f"- {label}: {f['value']}{date_str}")

            return "Known facts about this user:\n" + "\n".join(lines) if lines else ""
        except Exception as e:
            logger.error(f"[Mongo] format_facts_for_prompt failed: {e}", exc_info=True)
            return ""

    # ═══════════════════════════════════════════════════════
    # TASK OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def create_task(self, user_id: str, title: str, **kwargs) -> dict:
        """
        Create a new task.
        kwargs: due_date, priority, source
        """
        try:
            doc = TaskDocument(
                user_id=user_id,
                title=title,
                due_date=kwargs.get("due_date"),
                priority=kwargs.get("priority", "medium"),
                source=kwargs.get("source", "manual"),
            )
            payload = doc.model_dump()
            await self.tasks.insert_one(payload)
            logger.info(f"[Mongo] Task created: {doc.task_id} for user={user_id}")
            return _serialize(payload)
        except Exception as e:
            logger.error(f"[Mongo] create_task failed: {e}", exc_info=True)
            raise

    async def get_tasks(self, user_id: str, status: str = None) -> list:
        """
        Fetch tasks for a user, sorted by priority then creation date.
        status: 'pending' | 'completed' | None (all)
        """
        try:
            query: dict[str, Any] = {"user_id": user_id}
            if status:
                query["status"] = status

            priority_order = {"high": 1, "medium": 2, "low": 3}
            cursor = self.tasks.find(query).sort("created_at", -1)
            docs = [_serialize(doc) async for doc in cursor]

            # Sort by priority in Python (MongoDB doesn't support custom sort orders natively)
            docs.sort(key=lambda d: (priority_order.get(d.get("priority", "medium"), 2),))
            return docs
        except Exception as e:
            logger.error(f"[Mongo] get_tasks failed: {e}", exc_info=True)
            return []

    async def complete_task(self, task_id: str, user_id: str) -> bool:
        """Mark a task as completed. Returns True if updated."""
        try:
            result = await self.tasks.update_one(
                {"task_id": task_id, "user_id": user_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"[Mongo] complete_task failed: {e}", exc_info=True)
            return False

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task. Returns True if deleted."""
        try:
            result = await self.tasks.delete_one({"task_id": task_id, "user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"[Mongo] delete_task failed: {e}", exc_info=True)
            return False

    # ═══════════════════════════════════════════════════════
    # ACTIVITY OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def save_activity(self, user_id: str, raw_text: str, extracted: dict) -> dict:
        """
        Save a structured activity log.
        extracted: {emotion, activity, status, productivity, summary}
        """
        try:
            doc = ActivityDocument(
                user_id=user_id,
                raw_text=raw_text,
                emotion=extracted.get("emotion", "neutral"),
                activity=extracted.get("activity", ""),
                status=extracted.get("status", ""),
                productivity=extracted.get("productivity", ""),
                summary=extracted.get("summary", ""),
            )
            payload = doc.model_dump()
            await self.activities.insert_one(payload)
            logger.debug(f"[Mongo] Activity saved: {doc.activity_id}")
            return _serialize(payload)
        except Exception as e:
            logger.error(f"[Mongo] save_activity failed: {e}", exc_info=True)
            raise

    async def get_activities(self, user_id: str, limit: int = 20) -> list:
        """Fetch recent activities for a user."""
        try:
            cursor = (
                self.activities
                .find({"user_id": user_id})
                .sort("created_at", -1)
                .limit(limit)
            )
            return [_serialize(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"[Mongo] get_activities failed: {e}", exc_info=True)
            return []

    async def get_emotion_summary(self, user_id: str) -> dict:
        """
        Aggregate emotion counts for a user.
        Returns: {"happy": 3, "tired": 5, ...}
        """
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "emotion": {"$ne": ""}}},
                {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
            cursor = self.activities.aggregate(pipeline)
            return {doc["_id"]: doc["count"] async for doc in cursor}
        except Exception as e:
            logger.error(f"[Mongo] get_emotion_summary failed: {e}", exc_info=True)
            return {}

    # ═══════════════════════════════════════════════════════
    # MOOD OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def log_mood(
        self,
        user_id: str,
        mood: str,
        mood_score: int,
        **kwargs,
    ) -> dict:
        """
        Log a mood entry.
        kwargs: note, day_of_week, hour_of_day, source
        """
        try:
            now = datetime.utcnow()
            doc = MoodLogDocument(
                user_id=user_id,
                mood=mood.lower(),
                mood_score=mood_score,
                note=kwargs.get("note", ""),
                day_of_week=kwargs.get("day_of_week", now.strftime("%A")),
                hour_of_day=kwargs.get("hour_of_day", now.hour),
                source=kwargs.get("source", "manual"),
            )
            payload = doc.model_dump()
            await self.mood_logs.insert_one(payload)
            logger.debug(f"[Mongo] Mood logged: {mood} score={mood_score} user={user_id}")
            return _serialize(payload)
        except Exception as e:
            logger.error(f"[Mongo] log_mood failed: {e}", exc_info=True)
            raise

    async def get_mood_history(self, user_id: str, days: int = 30) -> list:
        """Fetch mood logs for the last N days."""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            cursor = (
                self.mood_logs
                .find({"user_id": user_id, "created_at": {"$gte": since}})
                .sort("created_at", 1)
            )
            return [_serialize(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"[Mongo] get_mood_history failed: {e}", exc_info=True)
            return []
