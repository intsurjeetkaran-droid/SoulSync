"""
SoulSync AI - Chat Service
Orchestrates: Redis cache → MongoDB → FAISS → Groq AI → MongoDB → Redis

Flow for send_message:
  1. Check Redis cache (skip for memory-sensitive queries)
  2. Get or create conversation in MongoDB
  3. Save user message to MongoDB
  4. Load recent chat history from MongoDB (last 5 turns)
  5. Load memory facts from MongoDB (with Redis cache)
  6. FAISS vector search for semantic context
  7. Call Groq AI with full context
  8. Save AI response to MongoDB
  9. Cache response in Redis
  10. Return full response dict
"""

from __future__ import annotations

import logging
from typing import Optional

from ..mongo.repository import MongoRepository
from ..redis.cache import RedisCacheManager

logger = logging.getLogger("soulsync.services.chat")


class ChatService:
    """
    High-level chat orchestration service.
    Depends on MongoRepository and RedisCacheManager.
    FAISS and Groq are imported lazily to avoid circular imports.
    """

    def __init__(self, mongo_repo: MongoRepository, redis_cache: RedisCacheManager):
        self.mongo = mongo_repo
        self.cache = redis_cache

    # ─── Send Message ─────────────────────────────────────

    async def send_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> dict:
        """
        Process a user message and return the AI response.

        Args:
            user_id         : unique user identifier
            message         : the user's message text
            conversation_id : existing conversation ID (creates new if None)
            use_cache       : whether to check/populate Redis cache

        Returns:
            dict with keys: response, conversation_id, message_id,
                            retrieved_memories, intent, stored_fact,
                            tasks_created, cached
        """
        if not message.strip():
            raise ValueError("Message cannot be empty")

        logger.info(f"[ChatService] user={user_id} | msg='{message[:80]}'")

        # ── Step 1: Check Redis cache ──────────────────────
        if use_cache:
            cached_response = await self.cache.get_cached_response(user_id, message)
            if cached_response:
                logger.info("[ChatService] Cache hit")
                return {
                    "response": cached_response,
                    "conversation_id": conversation_id,
                    "message_id": None,
                    "retrieved_memories": [],
                    "intent": "cached",
                    "stored_fact": None,
                    "tasks_created": [],
                    "cached": True,
                }

        # ── Step 2: Get or create conversation ────────────
        if conversation_id:
            conv = await self.mongo.get_conversation(conversation_id)
            if not conv:
                conv = await self.mongo.create_conversation(user_id, title=message[:50])
                conversation_id = conv["conversation_id"]
        else:
            conv = await self.mongo.create_conversation(user_id, title=message[:50])
            conversation_id = conv["conversation_id"]

        # ── Step 3: Save user message to MongoDB ──────────
        # Score importance and detect emotion/intent
        importance_score = 5
        emotion = "neutral"
        intent = "normal_chat"
        try:
            from backend.processing.scorer import score_memory
            score_result = score_memory(message, user_id, "user")
            importance_score = score_result.get("score", 5)
        except Exception:
            pass

        try:
            from backend.processing.extractor import extract_memory
            extracted = extract_memory(message)
            emotion = extracted.get("emotion", "neutral") or "neutral"
        except Exception:
            pass

        try:
            from backend.processing.intent_detector import detect_intent
            intent_result = detect_intent(message)
            intent = intent_result.get("intent", "normal_chat") if isinstance(intent_result, dict) else str(intent_result)
        except Exception:
            pass

        user_msg_doc = await self.mongo.save_message(
            user_id=user_id,
            conversation_id=conversation_id,
            role="user",
            content=message,
            importance_score=importance_score,
            emotion=emotion,
            intent=intent,
        )

        # ── Step 4: Load recent chat history ──────────────
        chat_history = await self.mongo.get_chat_history_turns(
            user_id=user_id,
            conversation_id=conversation_id,
            turns=5,
        )

        # ── Step 5: Load memory facts (Redis → MongoDB) ───
        memory_context = await self.cache.get_cached_facts(user_id)
        if not memory_context:
            memory_context = await self.mongo.format_facts_for_prompt(user_id)
            if memory_context:
                await self.cache.cache_facts(user_id, memory_context, ttl=300)

        # ── Step 6: FAISS vector search ───────────────────
        retrieved_memories: list = []
        try:
            from backend.retrieval.vector_store import search_memory, add_memory
            faiss_results = search_memory(user_id, message, top_k=3)
            retrieved_memories = [r["text"] for r in faiss_results]
            # Add user message to FAISS index
            add_memory(user_id, message)
        except Exception as e:
            logger.warning(f"[ChatService] FAISS search failed: {e}")

        # Build full memory context
        full_context = memory_context or ""
        if retrieved_memories:
            full_context += "\n\nRelevant past memories:\n" + "\n".join(
                f"- {m}" for m in retrieved_memories
            )

        # ── Step 7: Call Groq AI ──────────────────────────
        from backend.core.ai_service import generate_response
        ai_result = generate_response(
            user_input=message,
            memory_context=full_context,
            chat_history=chat_history,
        )
        response_text = ai_result["response"]

        # ── Step 8: Save AI response to MongoDB ───────────
        ai_msg_doc = await self.mongo.save_message(
            user_id=user_id,
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            importance_score=5,
            emotion="neutral",
            intent=intent,
        )

        # ── Step 9: Auto-log mood from emotion ────────────
        try:
            if emotion and emotion != "neutral":
                from backend.processing.mood_predictor import auto_log_mood_from_emotion
                auto_log_mood_from_emotion(user_id, emotion, note=message[:100])
        except Exception:
            pass

        # ── Step 10: Cache response in Redis ──────────────
        if use_cache and intent not in ("personal_info_query", "memory_query"):
            await self.cache.cache_chat_response(user_id, message, response_text)

        # ── Step 11: Auto-create tasks if task intent ─────
        tasks_created: list = []
        if intent == "task_command":
            try:
                from backend.tasks.task_detector import detect_tasks
                detected = detect_tasks(message)
                for task_data in detected:
                    task = await self.mongo.create_task(
                        user_id=user_id,
                        title=task_data["title"],
                        due_date=task_data.get("due_date"),
                        priority=task_data.get("priority", "medium"),
                        source="auto",
                    )
                    tasks_created.append(task)
                logger.info(f"[ChatService] Auto-created {len(tasks_created)} tasks")
            except Exception as e:
                logger.warning(f"[ChatService] Task auto-create failed: {e}")

        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "message_id": ai_msg_doc.get("message_id"),
            "retrieved_memories": retrieved_memories,
            "intent": intent,
            "stored_fact": None,
            "tasks_created": tasks_created,
            "cached": False,
        }

    # ─── Get Conversation History ─────────────────────────

    async def get_conversation_history(
        self,
        user_id: str,
        conversation_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Return paginated message history for a conversation.

        Returns:
            dict with keys: messages, page, page_size, total_fetched, conversation_id
        """
        skip = (page - 1) * page_size
        messages = await self.mongo.get_messages(
            conversation_id=conversation_id,
            limit=page_size,
            skip=skip,
        )
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "page": page,
            "page_size": page_size,
            "total_fetched": len(messages),
        }

    # ─── Get User Conversations ───────────────────────────

    async def get_user_conversations(
        self, user_id: str, limit: int = 20
    ) -> list:
        """
        Return recent conversations for a user.
        Checks Redis cache first.
        """
        # Try cache
        cached = await self.cache.get_recent_conversations(user_id)
        if cached is not None:
            return cached

        conversations = await self.mongo.get_conversations(user_id, limit=limit)

        # Cache for 5 minutes
        await self.cache.cache_recent_conversations(user_id, conversations, ttl=300)
        return conversations

    # ─── Delete Conversation ──────────────────────────────

    async def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.
        Also invalidates the user's conversation cache.
        """
        try:
            db = self.mongo.db
            await db.messages.delete_many({"conversation_id": conversation_id, "user_id": user_id})
            result = await db.conversations.delete_one(
                {"conversation_id": conversation_id, "user_id": user_id}
            )
            await self.cache.invalidate_user_cache(user_id)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"[ChatService] delete_conversation failed: {e}", exc_info=True)
            return False
