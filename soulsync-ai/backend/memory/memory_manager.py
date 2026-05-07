"""
SoulSync AI - Memory Manager (MongoDB)
=======================================

Central module for all memory operations in SoulSync AI.
Handles persistent storage of conversations, personal facts, and chat history
using MongoDB (Motor async driver) with sync wrappers for backward compatibility.

Key Features:
    - Persistent conversation storage in MongoDB
    - Automatic importance scoring for memories
    - Chat history retrieval with turn-based grouping
    - Keyword-based memory search
    - Earliest memory recall (chronological)
    - User existence validation

Architecture:
    - Uses Motor (async MongoDB driver) for non-blocking operations
    - Sync wrappers allow existing synchronous code to work unchanged
    - Importance scoring determines which memories to prioritize
    - All operations are user-isolated for privacy

Database Collections:
    - messages: All chat messages (user and assistant)
    - users: User profiles and metadata
    - memories: Personal facts and structured information

Usage:
    from backend.memory.memory_manager import (
        save_conversation,
        get_chat_history,
        get_memories,
        search_memories_by_keyword
    )
    
    # Save a conversation turn
    save_conversation("user123", "Hello!", "Hi there! How can I help?")
    
    # Get recent chat history
    history = get_chat_history("user123", turns=5)
    
    # Search for specific memories
    gym_memories = search_memories_by_keyword("user123", "gym")

Dependencies:
    - motor: Async MongoDB driver
    - backend.db.mongo.connection: MongoDB connection management
    - backend.processing.scorer: Memory importance scoring

Author: Surjeet Karan
Created: April 23, 2026
"""

import asyncio
import logging
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("soulsync.memory_manager")
logger.info("[Memory Manager] Module initializing...")


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _run(coro):
    """
    Run async coroutine safely from both sync and async contexts.
    
    This utility handles the complexity of running async MongoDB operations
    from synchronous code paths. It detects whether we're already in an async
    context and handles accordingly.
    
    Args:
        coro: Async coroutine to execute
        
    Returns:
        Result of the coroutine
        
    Raises:
        TimeoutError: If operation takes longer than 30 seconds
    """
    try:
        loop = asyncio.get_running_loop()
        # We're inside a running event loop (FastAPI) — use a thread
        logger.debug("[MemMgr] Running async operation in thread pool")
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=30)
    except RuntimeError:
        # No running loop — run directly
        logger.debug("[MemMgr] Running async operation directly")
        return asyncio.run(coro)


def _db():
    """
    Get MongoDB database handle.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
        
    Note:
        Lazy import prevents circular dependencies
    """
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


# ═══════════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_user_exists(user_id: str, name: str = None):
    """
    Ensure a user document exists in the database.
    
    Creates a user record if it doesn't exist, allowing legacy users
    (without formal registration) to have persistent storage.
    
    Args:
        user_id: Unique user identifier
        name: Optional display name (defaults to user_id)
        
    Note:
        This is a legacy function for backward compatibility.
        New users should go through proper authentication flow.
    """
    async def _run_inner():
        db = _db()
        
        # Check if user already exists
        existing = await db.users.find_one({"user_id": user_id})
        if existing:
            logger.debug(f"[MemMgr] User {user_id} already exists")
            return
        
        # Create new user document
        logger.info(f"[MemMgr] Creating legacy user: {user_id}")
        await db.users.insert_one({
            "user_id": user_id,
            "name": name or user_id,
            "email": f"{user_id}@legacy.soulsync.ai",
            "password_hash": "",  # Empty for legacy users
            "profile": {},
            "preferences": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
    
    try:
        _run(_run_inner())
    except Exception as e:
        logger.error(f"[MemMgr] ensure_user_exists failed for {user_id}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

def save_memory(
    user_id: str,
    role: str,
    message: str,
    importance_score: int = None,
    emotion: str = "neutral",
    intent: str = "normal_chat"
):
    """
    Save a single message to the user's memory.
    
    Each message is stored with metadata including importance score,
    emotion, and intent for later retrieval and analysis.
    
    Args:
        user_id: Unique user identifier
        role: Message role ("user" or "assistant")
        message: The message content
        importance_score: Priority score (0-15), auto-calculated if None
        emotion: Detected emotion from the message
        intent: Detected user intent
        
    Returns:
        str: The generated message_id if successful, None otherwise
        
    Note:
        Importance scoring is automatic if not provided.
        See backend.processing.scorer for scoring algorithm.
    """
    # Auto-calculate importance score if not provided
    if importance_score is None:
        try:
            from backend.processing.scorer import score_memory
            importance_score = score_memory(message, user_id, role).get("score", 5)
            logger.debug(f"[MemMgr] Auto-scored message: {importance_score}")
        except Exception as e:
            logger.warning(f"[MemMgr] Failed to score memory: {e}")
            importance_score = 5  # Default neutral score
    
    async def _run_inner():
        db = _db()
        message_id = str(uuid.uuid4())
        
        # Insert message document
        await db.messages.insert_one({
            "message_id": message_id,
            "conversation_id": f"legacy_{user_id}",
            "user_id": user_id,
            "role": role,
            "content": message,
            "importance_score": importance_score,
            "emotion": emotion,
            "intent": intent,
            "created_at": datetime.utcnow(),
        })
        
        logger.info(
            f"[MemMgr] Saved memory | user={user_id} | role={role} | "
            f"score={importance_score} | len={len(message)}"
        )
        return message_id
    
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[MemMgr] save_memory failed: {e}")
        return None


def save_conversation(user_id: str, user_message: str, ai_response: str):
    """
    Save a complete conversation turn (user message + AI response).
    
    This is the primary method for storing conversations. It ensures
    the user exists and saves both the user's message and the AI's response.
    
    Args:
        user_id: Unique user identifier
        user_message: The user's input message
        ai_response: The AI's generated response
        
    Example:
        save_conversation("user123", "I'm feeling tired", "I understand...")
    """
    logger.debug(f"[MemMgr] Saving conversation for user {user_id}")
    
    # Ensure user record exists
    ensure_user_exists(user_id)
    
    # Save both messages
    save_memory(user_id, "user", user_message)
    save_memory(user_id, "assistant", ai_response)


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════════

def get_memories(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve recent memories for a user.
    
    Returns memories in chronological order (oldest first) to maintain
    conversation flow context.
    
    Args:
        user_id: Unique user identifier
        limit: Maximum number of memories to return
        
    Returns:
        List of memory documents with fields:
            - id: MongoDB document ID
            - user_id: User identifier
            - role: "user" or "assistant"
            - message: Message content
            - importance_score: Priority score
            - created_at: Timestamp
            
    Note:
        Results are reversed to show oldest first (chronological order)
    """
    async def _run_inner():
        db = _db()
        
        # Query most recent memories first
        cursor = db.messages.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        
        docs = []
        async for doc in cursor:
            docs.append({
                "id": str(doc.get("_id", "")),
                "user_id": doc.get("user_id"),
                "role": doc.get("role"),
                "message": doc.get("content", ""),
                "importance_score": doc.get("importance_score", 5),
                "created_at": str(doc.get("created_at", "")),
            })
        
        # Reverse to show oldest first (chronological)
        return list(reversed(docs))
    
    try:
        result = _run(_run_inner())
        logger.debug(f"[MemMgr] Retrieved {len(result)} memories for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"[MemMgr] get_memories failed: {e}")
        return []


def get_earliest_memories(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve the earliest memories for a user (first interactions).
    
    Useful for answering questions like "What was my first experience?"
    or "When did we first talk about X?"
    
    Args:
        user_id: Unique user identifier
        limit: Maximum number of earliest memories to return
        
    Returns:
        List of earliest memory documents (chronological order)
    """
    async def _run_inner():
        db = _db()
        
        # Query oldest messages first
        cursor = (
            db.messages
            .find({"user_id": user_id, "role": "user"})
            .sort("created_at", 1)
            .limit(limit)
        )
        
        docs = []
        async for doc in cursor:
            docs.append({
                "id": str(doc.get("_id", "")),
                "role": doc.get("role"),
                "message": doc.get("content", ""),
                "importance_score": doc.get("importance_score", 5),
                "created_at": str(doc.get("created_at", "")),
            })
        
        return docs
    
    try:
        result = _run(_run_inner())
        logger.debug(f"[MemMgr] Retrieved {len(result)} earliest memories for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"[MemMgr] get_earliest_memories failed: {e}")
        return []


def search_memories_by_keyword(
    user_id: str,
    keyword: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search memories by keyword using regex pattern matching.
    
    Fallback search method when vector search (FAISS) doesn't find results.
    Case-insensitive search across message content.
    
    Args:
        user_id: Unique user identifier
        keyword: Search term (case-insensitive)
        limit: Maximum number of results
        
    Returns:
        List of matching memory documents (chronological order)
        
    Note:
        This is a fallback to FAISS vector search.
        For better semantic search, use the RAG engine.
    """
    async def _run_inner():
        db = _db()
        
        # Build case-insensitive regex pattern
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        
        # Search user messages
        cursor = (
            db.messages
            .find({"user_id": user_id, "role": "user", "content": {"$regex": pattern}})
            .sort("created_at", 1)
            .limit(limit)
        )
        
        docs = []
        async for doc in cursor:
            docs.append({
                "id": str(doc.get("_id", "")),
                "role": doc.get("role"),
                "message": doc.get("content", ""),
                "importance_score": doc.get("importance_score", 5),
                "created_at": str(doc.get("created_at", "")),
            })
        
        return docs
    
    try:
        result = _run(_run_inner())
        logger.debug(f"[MemMgr] Keyword search '{keyword}' found {len(result)} results for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"[MemMgr] search_memories_by_keyword failed: {e}")
        return []


def get_chat_history(user_id: str, turns: int = 5) -> List[tuple]:
    """
    Retrieve recent chat history as (user_msg, bot_msg) tuples.
    
    Groups consecutive user/assistant messages into conversation turns
    for use as context in AI generation.
    
    Args:
        user_id: Unique user identifier
        turns: Number of conversation turns to return
        
    Returns:
        List of (user_message, assistant_message) tuples
        
    Example:
        history = get_chat_history("user123", turns=3)
        # Returns: [("Hello", "Hi!"), ("How are you?", "I'm good!"), ...]
    """
    # Get recent memories (2 per turn)
    memories = get_memories(user_id, limit=turns * 2)
    
    # Group into (user, assistant) pairs
    history = []
    i = 0
    while i < len(memories) - 1:
        if memories[i]["role"] == "user" and memories[i+1]["role"] == "assistant":
            history.append((memories[i]["message"], memories[i+1]["message"]))
            i += 2
        else:
            i += 1
    
    # Return only the requested number of turns
    result = history[-turns:]
    logger.debug(f"[MemMgr] Chat history for user {user_id}: {len(result)} turns")
    return result


def get_memory_count(user_id: str) -> int:
    """
    Get total number of memories for a user.
    
    Useful for statistics and determining if a user has enough
    data for meaningful personalization.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Total count of messages (user + assistant)
    """
    async def _run_inner():
        db = _db()
        return await db.messages.count_documents({"user_id": user_id})
    
    try:
        count = _run(_run_inner())
        logger.debug(f"[MemMgr] Memory count for user {user_id}: {count}")
        return count
    except Exception as e:
        logger.error(f"[MemMgr] get_memory_count failed: {e}")
        return 0


# ─── Module Initialization Complete ───────────────────────────────────────────
logger.info("[Memory Manager] Module initialized successfully")