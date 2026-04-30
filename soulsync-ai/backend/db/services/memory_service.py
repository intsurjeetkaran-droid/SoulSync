"""
SoulSync AI - Memory Service
Manages personal facts and semantic memory retrieval.

Storage:
  - MongoDB memories collection for structured facts
  - FAISS per-user index for semantic vector search
  - Redis for caching formatted facts

Retrieval strategy:
  1. FAISS semantic search (primary)
  2. MongoDB keyword fallback (if FAISS returns nothing)
"""

from __future__ import annotations

import logging
from typing import Optional

from ..mongo.repository import MongoRepository
from ..redis.cache import RedisCacheManager

logger = logging.getLogger("soulsync.services.memory")


class MemoryService:
    """
    High-level memory management service.
    Combines MongoDB structured facts with FAISS vector search.
    """

    def __init__(self, mongo_repo: MongoRepository, redis_cache: RedisCacheManager):
        self.mongo = mongo_repo
        self.cache = redis_cache

    # ─── Store Fact ───────────────────────────────────────

    async def store_fact(
        self,
        user_id: str,
        key: str,
        value: str,
        source_text: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Store a personal fact in MongoDB and invalidate the facts cache.

        Args:
            user_id     : unique user identifier
            key         : fact key (name, goal, job, etc.)
            value       : fact value
            source_text : original sentence that triggered this fact
            context     : category (identity, goal, preference, career)

        Returns:
            The stored memory document dict.
        """
        try:
            result = await self.mongo.store_memory_fact(
                user_id=user_id,
                key=key,
                value=value,
                source_text=source_text,
                context=context,
            )
            # Invalidate cached facts so next prompt gets fresh data
            await self.cache.invalidate_facts_cache(user_id)
            logger.info(f"[MemoryService] Stored fact: user={user_id} key={key}")
            return result
        except Exception as e:
            logger.error(f"[MemoryService] store_fact failed: {e}", exc_info=True)
            raise

    # ─── Get Facts for Prompt ─────────────────────────────

    async def get_facts_for_prompt(self, user_id: str) -> str:
        """
        Return formatted memory facts for AI prompt injection.
        Checks Redis cache first; falls back to MongoDB.

        Returns:
            Formatted string like "Known facts about this user:\n- Name: Rohit\n..."
            Empty string if no facts found.
        """
        # Try Redis cache first
        cached = await self.cache.get_cached_facts(user_id)
        if cached is not None:
            logger.debug(f"[MemoryService] Facts cache hit for user={user_id}")
            return cached

        # Fetch from MongoDB and cache
        facts_text = await self.mongo.format_facts_for_prompt(user_id)
        if facts_text:
            await self.cache.cache_facts(user_id, facts_text, ttl=300)

        return facts_text

    # ─── Get All Facts ────────────────────────────────────

    async def get_all_facts(self, user_id: str, key: Optional[str] = None) -> list:
        """
        Return all memory facts for a user, optionally filtered by key prefix.
        """
        return await self.mongo.get_memory_facts(user_id, key=key)

    # ─── Get Single Fact ──────────────────────────────────

    async def get_single_fact(self, user_id: str, key: str) -> Optional[str]:
        """Return the most recent value for a specific key."""
        return await self.mongo.get_single_fact(user_id, key)

    # ─── Search Memories ──────────────────────────────────

    async def search_memories(
        self, user_id: str, query: str, top_k: int = 5
    ) -> list:
        """
        Search memories using FAISS semantic search with MongoDB keyword fallback.

        Returns:
            List of dicts with keys: text/content, score, source
        """
        results = []

        # ── Primary: FAISS semantic search ────────────────
        try:
            from backend.retrieval.vector_store import search_memory
            faiss_results = search_memory(user_id, query, top_k=top_k)
            if faiss_results:
                results = [
                    {"content": r["text"], "score": r["score"], "source": "faiss"}
                    for r in faiss_results
                ]
                logger.debug(f"[MemoryService] FAISS returned {len(results)} results")
                return results
        except Exception as e:
            logger.warning(f"[MemoryService] FAISS search failed: {e}")

        # ── Fallback: MongoDB keyword search ──────────────
        try:
            mongo_results = await self.mongo.search_messages(
                user_id=user_id, keyword=query, limit=top_k
            )
            results = [
                {
                    "content": r.get("content", ""),
                    "score": 0.5,
                    "source": "mongodb",
                }
                for r in mongo_results
            ]
            logger.debug(f"[MemoryService] MongoDB fallback returned {len(results)} results")
        except Exception as e:
            logger.warning(f"[MemoryService] MongoDB keyword search failed: {e}")

        return results

    # ─── Get Earliest Memory ─────────────────────────────

    async def get_earliest_memory(self, user_id: str) -> Optional[dict]:
        """
        Return the earliest message the user sent.
        Used for 'what was the first thing I told you?' queries.
        """
        messages = await self.mongo.get_earliest_messages(user_id, limit=1)
        return messages[0] if messages else None

    # ─── Get Earliest Messages ────────────────────────────

    async def get_earliest_messages(self, user_id: str, limit: int = 3) -> list:
        """Return the N oldest user messages in chronological order."""
        return await self.mongo.get_earliest_messages(user_id, limit=limit)

    # ─── Build Direct Answer ──────────────────────────────

    async def build_direct_answer(
        self, user_id: str, query_key: Optional[str]
    ) -> Optional[str]:
        """
        Build a direct answer from stored facts without calling the AI.
        Mirrors the logic from the legacy personal_info.py.

        Args:
            user_id   : unique user identifier
            query_key : specific key to look up, '__earliest__' for first memory,
                        None for all facts

        Returns:
            Formatted answer string, or None if no data found.
        """
        key_labels = {
            "name": "Name", "age": "Age", "goal": "Goal", "dream": "Dream",
            "aim": "Aim", "job": "Job / Profession", "hobby": "Hobby",
            "interest": "Interest", "location": "Location",
            "email": "Email", "phone": "Phone",
        }

        # ── Earliest memory ───────────────────────────────
        if query_key == "__earliest__":
            earliest = await self.get_earliest_messages(user_id, limit=3)
            if not earliest:
                return None
            lines = [
                f'• [{m.get("created_at", "")[:10]}] "{m.get("content", "")}"'
                for m in earliest
            ]
            return (
                "Here are the earliest things you shared with me:\n"
                + "\n".join(lines)
                + "\n\nThese are your first memories in SoulSync. 🧠"
            )

        # ── All facts ─────────────────────────────────────
        if query_key is None:
            facts = await self.get_all_facts(user_id)
            if not facts:
                return None
            lines = []
            for f in facts:
                raw_key = f["key"].split("_")[0]
                label = key_labels.get(raw_key, raw_key.replace("_", " ").title())
                date_str = f" [{f['event_date'][:10]}]" if f.get("event_date") else ""
                lines.append(f"• {label}: {f['value']}{date_str}")
            return "Here's what I know about you:\n" + "\n".join(lines) + " 😊"

        # ── Goals timeline ────────────────────────────────
        if query_key == "goal":
            goals = await self.get_all_facts(user_id, key="goal")
            if not goals:
                return None
            if len(goals) == 1:
                g = goals[0]
                date_str = f" (set on {g['event_date'][:10]})" if g.get("event_date") else ""
                return f"Your goal is: {g['value']}{date_str} 💪"
            lines = []
            for g in goals:
                date_str = (g.get("event_date") or g.get("created_at", ""))[:10]
                lines.append(f"• [{date_str}] {g['value']}")
            return "Your goals over time:\n" + "\n".join(lines) + " 💪"

        # ── Specific key ──────────────────────────────────
        rows = await self.get_all_facts(user_id, key=query_key)
        if not rows:
            return None

        f = rows[0]
        value = f["value"]
        label = key_labels.get(query_key, query_key.replace("_", " ").title())
        date_str = ""
        if f.get("event_date"):
            date_str = f" (as of {f['event_date'][:10]})"
        elif f.get("updated_at"):
            date_str = f" (last updated {f['updated_at'][:10]})"

        answers = {
            "name": f"Your name is {value} 😊",
            "age": f"You are {value} years old{date_str}.",
            "goal": f"Your goal is: {value}{date_str} 💪",
            "dream": f"Your dream is: {value}{date_str} ✨",
            "aim": f"Your aim is: {value}{date_str}",
            "job": f"You work as: {value}{date_str}",
            "hobby": f"Your hobby is: {value}",
            "interest": f"You enjoy: {value}",
            "location": f"You live in {value}{date_str}.",
            "email": f"Your email is {value}.",
            "phone": f"Your phone number is {value}.",
        }
        return answers.get(query_key, f"Your {label.lower()} is: {value}{date_str}")
