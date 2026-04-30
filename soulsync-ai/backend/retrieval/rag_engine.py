"""
SoulSync AI - RAG Engine (v3)
Intent-aware + Collection-aware Retrieval-Augmented Generation.
"""

import re
import logging
from backend.retrieval.vector_store         import search_memory, add_memory
from backend.core.ai_service                import generate_response
from backend.processing.intent_detector     import detect_intent
from backend.memory.personal_info           import (
    store_personal_info, format_for_prompt, build_direct_answer
)
from backend.memory.collection_store        import save_to_collection
from backend.memory.recall_engine           import recall
from backend.memory.life_timeline           import add_to_timeline

logger = logging.getLogger("soulsync.rag_engine")


# ─── Groq-powered task completion detector ────────────────

def _groq_detect_task_completion(user_message: str, pending_tasks: list) -> dict | None:
    """
    Use Groq to understand if a natural language message (any language)
    implies completing or doing a pending task.

    Returns:
        {"task_id": int, "task_title": str, "confidence": float}
        or None if no match found.
    """
    if not pending_tasks:
        return None

    try:
        from backend.core.ai_service import client, GROQ_MODEL

        task_list = "\n".join(
            f"{i+1}. [ID:{t['id']}] {t['title']}"
            for i, t in enumerate(pending_tasks[:10])
        )

        prompt = (
            f"The user said: \"{user_message}\"\n\n"
            f"Their pending tasks are:\n{task_list}\n\n"
            f"Does this message imply they completed or did one of these tasks? "
            f"The message may be in any language (Hindi, Hinglish, English, etc.).\n\n"
            f"If yes, respond with ONLY this JSON: "
            f'{{\"matched\": true, \"task_id\": <number>, \"task_title\": \"<title>\", \"confidence\": <0.0-1.0>}}\n'
            f"If no match, respond with ONLY: {{\"matched\": false}}\n"
            f"No explanation. JSON only."
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a task completion detector. Respond only with JSON."},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=80,
            temperature=0.1,
        )

        import json
        raw = response.choices[0].message.content.strip()
        # Extract JSON
        json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            if parsed.get("matched") and parsed.get("task_id"):
                return {
                    "task_id"    : int(parsed["task_id"]),
                    "task_title" : parsed.get("task_title", ""),
                    "confidence" : float(parsed.get("confidence", 0.8)),
                }
    except Exception as e:
        logger.warning(f"[RAG] Groq task detection failed: {e}")

    return None


# ─── Task management handler ──────────────────────────────

def _handle_task_manage(user_id: str, op: str, keyword: str,
                        original_msg: str, lang: dict = None) -> dict:
    """
    Handle task CRUD from natural language — any language.
    1. Try keyword matching first (fast)
    2. Fall back to Groq semantic matching (handles Hinglish, implicit completion)
    3. On completion: mark done + save to memory/timeline (never delete)
    4. On delete: remove from list only
    """
    from backend.tasks.task_manager import (
        get_tasks, complete_task, delete_task
    )

    tasks = get_tasks(user_id, status="pending")
    if not tasks:
        return {
            "response"           : "You don't have any pending tasks right now. 📋",
            "retrieved_memories" : [], "memory_count": 0,
            "used_rag"           : False, "intent": "task_manage",
            "stored_fact"        : None, "task_action": None,
        }

    # ── Step 1: Keyword matching ───────────────────────────
    keyword_lower = keyword.lower().strip()
    best_task     = None
    best_score    = 0

    for task in tasks:
        title_lower = task["title"].lower()
        kw_words    = set(keyword_lower.split())
        t_words     = set(title_lower.split())
        score       = len(kw_words & t_words)
        if keyword_lower in title_lower or title_lower in keyword_lower:
            score += 5
        if score > best_score:
            best_score = score
            best_task  = task

    # ── Step 2: Groq fallback if no keyword match ──────────
    if not best_task or best_score == 0:
        groq_match = _groq_detect_task_completion(original_msg, tasks)
        if groq_match and groq_match["confidence"] >= 0.6:
            # Find the task by ID
            matched_id = groq_match["task_id"]
            for t in tasks:
                if t["id"] == matched_id:
                    best_task  = t
                    best_score = 10   # high confidence
                    # Groq detected completion — override op
                    op = "complete"
                    break

    # ── Step 3: Still no match — ask user ─────────────────
    if not best_task or best_score == 0:
        task_list = "\n".join(f"• {t['title']}" for t in tasks[:5])
        return {
            "response"           : f"I couldn't figure out which task you meant. Here are your pending tasks:\n{task_list}\n\nWhich one did you complete?",
            "retrieved_memories" : [], "memory_count": 0,
            "used_rag"           : False, "intent": "task_manage",
            "stored_fact"        : None, "task_action": None,
        }

    task_title = best_task["title"]
    task_id    = best_task["id"]

    if not lang:
        lang = {"is_hindi": False, "code": "en"}
    is_hindi = lang.get("is_hindi", False)

    # ── Step 4: Apply operation ────────────────────────────

    if op == "delete":
        delete_task(task_id, user_id)
        _save_task_to_memory(user_id, task_title, original_msg, "removed")
        response = (
            f"Theek hai! **{task_title}** task list se hata diya. 🗑️\nYaad ke liye save kar liya hai."
            if is_hindi else
            f"Removed **{task_title}** from your task list. 🗑️\nI've kept a note of it in your memory."
        )
        action = {"op": "deleted", "task_id": task_id, "title": task_title}

    elif op == "complete":
        complete_task(task_id, user_id)
        _save_task_to_memory(user_id, task_title, original_msg, "completed")
        response = (
            f"Wah! **{task_title}** complete ho gaya ✅\nYeh memory mein save kar liya — kabhi bhi dekh sakte ho."
            if is_hindi else
            f"Amazing! I've marked **{task_title}** as done ✅\nAnd I've saved this as a memory — you can always look back on it."
        )
        action = {"op": "completed", "task_id": task_id, "title": task_title}

    elif op in ("priority_high", "priority_low", "priority_medium"):
        priority_map = {"priority_high": "high", "priority_low": "low", "priority_medium": "medium"}
        new_priority = priority_map[op]
        import asyncio
        from backend.db.mongo.connection import get_mongo_db
        async def _update_priority():
            db = get_mongo_db()
            await db.tasks.update_one(
                {"$or": [{"task_id": str(task_id)}, {"task_id": task_id}], "user_id": user_id},
                {"$set": {"priority": new_priority}}
            )
        try:
            asyncio.get_event_loop().run_until_complete(_update_priority())
        except Exception:
            pass
        emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[new_priority]
        response = (
            f"Ho gaya! **{task_title}** ab {emoji} **{new_priority}** priority pe hai."
            if is_hindi else
            f"Updated! **{task_title}** is now {emoji} **{new_priority}** priority."
        )
        action = {"op": f"priority_{new_priority}", "task_id": task_id, "title": task_title}

    else:
        response = (
            f"**{task_title}** ke saath kya karna hai? Complete karna hai ya delete?"
            if is_hindi else
            f"I'm not sure what to do with **{task_title}**. Did you want to complete or delete it?"
        )
        action = None

    return {
        "response"           : response,
        "retrieved_memories" : [], "memory_count": 0,
        "used_rag"           : False, "intent": "task_manage",
        "stored_fact"        : None, "task_action": action,
    }


def _save_task_to_memory(user_id: str, task_title: str,
                         original_msg: str, status: str):
    """
    Save a completed/removed task to memory + life timeline.
    This ensures the user can always recall what they did,
    even after the task is gone from the task list.
    """
    try:
        from backend.memory.memory_manager import save_memory
        from datetime import date

        # Save the original message to memories table
        save_memory(user_id, "user", original_msg, importance_score=6)

        # Save a structured achievement/experience to collection store
        if status == "completed":
            collection = "achievement"
            content    = f"Completed task: {task_title}. Original message: {original_msg}"
        else:
            collection = "experience"
            content    = f"Removed task: {task_title}. Original message: {original_msg}"

        save_to_collection(
            user_id             = user_id,
            text                = content,
            override_collection = collection,
            override_date       = date.today(),
        )

        # Add to life timeline
        add_to_timeline(
            user_id         = user_id,
            content         = original_msg,
            collection_type = collection,
            event_date      = date.today(),
            source          = "chat",
        )

        logger.info(f"[RAG] Task memory saved: user={user_id} | task={task_title} | status={status}")

    except Exception as e:
        logger.warning(f"[RAG] Task memory save failed (non-critical): {e}")


# ─── Format RAG Memory Context ────────────────────────────

def format_rag_context(retrieved_memories: list) -> str:
    """
    Convert retrieved FAISS memory dicts into a readable context string.
    """
    if not retrieved_memories:
        return ""

    lines = []
    for i, mem in enumerate(retrieved_memories, 1):
        lines.append(f"{i}. {mem['text']}")

    return "Relevant past conversation context:\n" + "\n".join(lines)


# ─── Main RAG Chat ────────────────────────────────────────

def rag_chat(user_id: str, user_message: str,
             chat_history: list = None, top_k: int = 3) -> dict:
    """
    Intent-aware RAG pipeline.

    Flow:
      1. Detect intent
      2. personal_info_store → store fact, return confirmation (no AI)
      3. personal_info_query → DB lookup → direct answer or AI fallback
      4. normal_chat         → vector search + AI with full context

    Returns:
        dict with response, retrieved_memories, memory_count, used_rag,
              intent, stored_fact
    """
    intent_result = detect_intent(user_message)
    intent        = intent_result["intent"]

    # Detect language once — reuse for all AI calls in this request
    from backend.processing.language_detector import detect_language
    lang = detect_language(user_message)

    logger.info(f"[RAG] user={user_id} | intent={intent} | lang={lang['code']} | "
                f"key={intent_result.get('key')} | msg='{user_message[:60]}'")

    # ── INTENT: Store personal info ────────────────────────
    if intent == "personal_info_store":
        key   = intent_result["key"]
        value = intent_result["value"]

        store_personal_info(
            user_id     = user_id,
            key         = key,
            value       = value,
            source_text = user_message
        )

        # Also save to collection store (personal_fact type) + FAISS + timeline
        try:
            save_to_collection(user_id, user_message, override_collection="personal_fact")
            add_to_timeline(user_id, user_message, "personal_fact", source="chat")
        except Exception:
            pass
        add_memory(user_id, user_message)

        label = key.replace("_", " ").title()

        # Respond in user's language
        if lang.get("is_hindi"):
            response_text = (
                f"Theek hai! Maine aapka {label} save kar liya: **{value}** 📝\n"
                f"Main yeh hamesha yaad rakhunga."
            )
        else:
            response_text = (
                f"Got it! I've saved your {label}: **{value}** 📝\n"
                f"I'll remember this for all future conversations."
            )

        logger.info(f"[RAG] Stored personal info: {key}={value}")
        return {
            "response"           : response_text,
            "retrieved_memories" : [],
            "memory_count"       : 0,
            "used_rag"           : False,
            "intent"             : intent,
            "stored_fact"        : {"key": key, "value": value},
        }

    # ── INTENT: Query personal info ────────────────────────
    if intent == "personal_info_query":
        query_key = intent_result.get("key")

        # Step 1: Try recall engine (handles chronological + monthly + collection)
        recall_result = recall(user_id, user_message)
        if recall_result and recall_result.get("found"):
            logger.info(f"[RAG] Recall engine answered: source={recall_result['source']}")
            return {
                "response"           : recall_result["answer"],
                "retrieved_memories" : [],
                "memory_count"       : 0,
                "used_rag"           : True,
                "intent"             : intent,
                "stored_fact"        : None,
            }

        # Step 2: Direct DB answer from personal_info table
        direct_answer = build_direct_answer(user_id, query_key)
        if direct_answer:
            logger.info(f"[RAG] Direct answer from DB: key={query_key}")
            return {
                "response"           : direct_answer,
                "retrieved_memories" : [],
                "memory_count"       : 0,
                "used_rag"           : False,
                "intent"             : intent,
                "stored_fact"        : None,
            }

        # Step 3: AI fallback with personal context
        logger.info(f"[RAG] No data found for key={query_key}, using AI fallback")
        personal_ctx = format_for_prompt(user_id)
        result = generate_response(
            user_input     = user_message,
            memory_context = personal_ctx,
            chat_history   = chat_history or [],
            detected_lang  = lang,
        )
        add_memory(user_id, user_message)
        return {
            "response"           : result["response"],
            "retrieved_memories" : [],
            "memory_count"       : 0,
            "used_rag"           : bool(personal_ctx),
            "intent"             : intent,
            "stored_fact"        : None,
        }

    # ── INTENT: Task management (delete/complete/priority) ─
    if intent == "task_manage":
        op      = intent_result.get("key", "complete")
        keyword = intent_result.get("value", "")
        result  = _handle_task_manage(user_id, op, keyword, user_message, lang)
        add_memory(user_id, user_message)
        return result

    # ── INTENT: Normal chat (+ task_command) ──────────────
    # Save to typed collection store + life timeline (non-blocking)
    try:
        meta = save_to_collection(user_id, user_message)
        add_to_timeline(
            user_id         = user_id,
            content         = user_message,
            collection_type = meta.get("collection", "conversation"),
            event_date      = meta.get("event_date"),
            source          = "chat",
        )
    except Exception as e:
        logger.warning(f"[RAG] Collection/timeline save failed (non-critical): {e}")

    # ── Passive task completion check ─────────────────────
    # Even in normal_chat, check if the message implies completing a task.
    # This catches Hinglish/informal completions like "aaj shaadi attend kar li"
    passive_task_action = None
    try:
        from backend.tasks.task_manager import get_tasks
        pending = get_tasks(user_id, status="pending")
        if pending:
            groq_match = _groq_detect_task_completion(user_message, pending)
            if groq_match and groq_match["confidence"] >= 0.75:
                from backend.tasks.task_manager import complete_task
                complete_task(groq_match["task_id"], user_id)
                _save_task_to_memory(user_id, groq_match["task_title"],
                                     user_message, "completed")
                passive_task_action = {
                    "op"      : "completed",
                    "task_id" : groq_match["task_id"],
                    "title"   : groq_match["task_title"],
                }
                logger.info(f"[RAG] Passive task completion: {groq_match['task_title']}")
    except Exception as e:
        logger.warning(f"[RAG] Passive task check failed (non-critical): {e}")

    # Build full memory context: personal facts + vector search
    # Layer 1: Structured personal facts
    personal_ctx = format_for_prompt(user_id)

    # Layer 2: Semantic vector search for relevant past messages
    # top_k=5 gives broader recall for users with large histories
    retrieved = search_memory(user_id, user_message, top_k=5)
    rag_ctx   = format_rag_context(retrieved)

    # Layer 3: DB keyword fallback — if FAISS found nothing, try
    # extracting key nouns from the query and doing a text search
    if not retrieved:
        from backend.memory.memory_manager import search_memories_by_keyword
        import re
        # Extract meaningful words (4+ chars, not stopwords)
        stopwords = {"what", "when", "where", "that", "this", "with", "have",
                     "been", "from", "they", "were", "will", "about", "your",
                     "tell", "know", "first", "thing", "experience", "shared"}
        words = re.findall(r'\b[a-z]{4,}\b', user_message.lower())
        keywords = [w for w in words if w not in stopwords]
        for kw in keywords[:3]:
            db_results = search_memories_by_keyword(user_id, kw, limit=3)
            if db_results:
                db_lines = [f'{i+1}. [{str(r["created_at"])[:10]}] {r["message"]}'
                            for i, r in enumerate(db_results)]
                rag_ctx = "Relevant past memories (keyword match):\n" + "\n".join(db_lines)
                retrieved = [{"text": r["message"], "score": 0.0} for r in db_results]
                logger.info(f"[RAG] DB keyword fallback hit: '{kw}' → {len(db_results)} results")
                break

    logger.info(f"[RAG] Vector search: {len(retrieved)} relevant memories "
                f"(threshold filtered)")

    # Combine both context layers
    memory_parts = []
    if personal_ctx:
        memory_parts.append(personal_ctx)
    if rag_ctx:
        memory_parts.append(rag_ctx)

    full_memory_context = "\n\n".join(memory_parts)

    if full_memory_context:
        logger.info(f"[RAG] Injecting {len(full_memory_context)} chars of memory context")
    else:
        logger.info("[RAG] No memory context available")

    # Generate AI response
    result = generate_response(
        user_input     = user_message,
        memory_context = full_memory_context,
        chat_history   = chat_history or [],
        detected_lang  = lang,
    )

    # Store message in vector store for future retrieval
    add_memory(user_id, user_message)

    return {
        "response"           : result["response"],
        "retrieved_memories" : retrieved,
        "memory_count"       : len(retrieved),
        "used_rag"           : bool(full_memory_context),
        "intent"             : intent,
        "stored_fact"        : None,
    }
