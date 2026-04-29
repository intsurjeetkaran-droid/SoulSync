"""
SoulSync AI - Chat API Router
Handles /chat endpoint

Flow:
  1. Detect intent (personal_info_store / query / task / normal_chat)
  2. Route through intent-aware RAG engine
  3. Save conversation to DB + vector store
  4. Return response with full debug metadata
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.retrieval.rag_engine      import rag_chat
from backend.memory.memory_manager     import save_conversation, get_chat_history
from backend.retrieval.vector_store    import add_memory
from backend.tasks.task_manager        import auto_create_tasks
from backend.tasks.task_detector       import is_task_message
from backend.utils.cache               import response_cache

logger = logging.getLogger("soulsync.chat")
router = APIRouter()

# ─── Schemas ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id    : str
    message    : str
    use_memory : bool = True   # use DB history as context
    use_rag    : bool = True   # use vector search for personalization


class ChatResponse(BaseModel):
    user_id             : str
    message             : str
    response            : str
    memory_used         : bool
    rag_used            : bool
    retrieved_memories  : list
    tasks_created       : list
    intent              : Optional[str] = None
    stored_fact         : Optional[dict] = None
    task_action         : Optional[dict] = None


# ─── /chat Endpoint ───────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for SoulSync AI.

    Flow:
      1. Load recent chat history from DB
      2. Detect intent → route through RAG engine
      3. Save conversation to DB + vector store
      4. Auto-detect tasks (only for task_command intent)
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    logger.info(f"[Chat] user={request.user_id} | msg='{request.message[:80]}'")

    try:
        # Step 0: Check cache (skip for memory-sensitive queries)
        cached = response_cache.get(request.user_id, request.message)
        if cached and not request.use_memory:
            logger.info("[Chat] Cache hit")
            return ChatResponse(
                user_id=request.user_id,
                message=request.message,
                response=cached,
                memory_used=False,
                rag_used=False,
                retrieved_memories=[],
                tasks_created=[],
                intent="cached",
            )

        # Step 1: Load recent chat history from DB
        chat_history = []
        if request.use_memory:
            chat_history = get_chat_history(request.user_id, turns=5)
            logger.info(f"[Chat] Loaded {len(chat_history)} history turns")

        if request.use_rag:
            # Step 2: Intent-aware RAG pipeline
            result = rag_chat(
                user_id=request.user_id,
                user_message=request.message,
                chat_history=chat_history,
                top_k=3
            )
            response_text      = result["response"]
            retrieved_memories = result["retrieved_memories"]
            rag_used           = result["used_rag"]
            intent             = result.get("intent", "normal_chat")
            stored_fact        = result.get("stored_fact")
            task_action        = result.get("task_action")

        else:
            # Simple chat without RAG
            from backend.core.ai_service import generate_response
            gen = generate_response(
                user_input=request.message,
                memory_context="",
                chat_history=chat_history
            )
            response_text      = gen["response"]
            retrieved_memories = []
            rag_used           = False
            intent             = "normal_chat"
            stored_fact        = None
            task_action        = None
            add_memory(request.user_id, request.message)

        logger.info(f"[Chat] intent={intent} | rag_used={rag_used} | "
                    f"response_len={len(response_text)}")

        # Step 3: Save to DB memory
        save_conversation(
            user_id=request.user_id,
            user_message=request.message,
            ai_response=response_text
        )

        # Step 4: Auto-log mood from extracted emotion (non-critical)
        try:
            from backend.processing.extractor import extract_memory
            from backend.processing.mood_predictor import auto_log_mood_from_emotion
            extracted = extract_memory(request.message)
            if extracted.get("emotion") and extracted["emotion"] != "neutral":
                auto_log_mood_from_emotion(
                    request.user_id,
                    extracted["emotion"],
                    note=request.message[:100]
                )
        except Exception:
            pass

        # Step 5: Cache non-RAG responses
        if not rag_used:
            response_cache.set(request.user_id, request.message, response_text)

        # Step 6: Auto-create tasks ONLY for task_command intent
        tasks_created = []
        if intent == "task_command":
            tasks_created = auto_create_tasks(request.user_id, request.message)
            logger.info(f"[Chat] Tasks created: {len(tasks_created)}")

        return ChatResponse(
            user_id=request.user_id,
            message=request.message,
            response=response_text,
            memory_used=request.use_memory,
            rag_used=rag_used,
            retrieved_memories=retrieved_memories,
            tasks_created=tasks_created,
            intent=intent,
            stored_fact=stored_fact,
            task_action=task_action,
        )

    except Exception as e:
        logger.error(f"[Chat] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ─── /health Endpoint ─────────────────────────────────────

@router.get("/health")
async def health():
    return {
        "status" : "ok",
        "module" : "Intent-aware RAG + Memory",
        "version": "2.0.0"
    }
