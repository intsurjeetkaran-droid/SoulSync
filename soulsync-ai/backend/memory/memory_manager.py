"""
SoulSync AI - Memory Manager
Handles all memory operations:
  - ensure_user_exists : auto-create user if not present
  - save_memory        : store a single message
  - save_conversation  : store user + assistant turn together
  - get_memories       : fetch recent memories for a user
  - get_chat_history   : return memories as (user, bot) pairs for model
"""

from datetime import datetime
from backend.memory.database import get_connection, get_cursor


# ─── User Management ──────────────────────────────────────

def ensure_user_exists(user_id: str, name: str = None):
    """
    Insert user if not already in DB.
    Safe to call on every request.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO users (user_id, name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO NOTHING;
            """,
            (user_id, name or user_id)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


# ─── Save Memory ──────────────────────────────────────────

def save_memory(user_id: str, role: str, message: str,
                importance_score: int = None):
    """
    Save a single message to the memories table.
    Auto-scores importance if not provided.

    Args:
        user_id          : unique user identifier
        role             : 'user' or 'assistant'
        message          : the message text
        importance_score : override score (auto-calculated if None)
    """
    # Auto-calculate importance score
    if importance_score is None:
        from backend.processing.scorer import score_memory
        result           = score_memory(message, user_id, role)
        importance_score = result["score"]

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO memories (user_id, role, message, importance_score)
            VALUES (%s, %s, %s, %s);
            """,
            (user_id, role, message, importance_score)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def save_conversation(user_id: str, user_message: str, ai_response: str):
    """
    Save a full conversation turn (user + assistant) in one call.
    Ensures user exists first.
    """
    ensure_user_exists(user_id)
    save_memory(user_id, "user",      user_message)
    save_memory(user_id, "assistant", ai_response)


# ─── Fetch Memory ─────────────────────────────────────────

def get_memories(user_id: str, limit: int = 20) -> list:
    """
    Fetch the most recent memories for a user.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, user_id, role, message,
                   COALESCE(importance_score, 5) as importance_score,
                   created_at
            FROM memories
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """,
            (user_id, limit)
        )
        rows = cur.fetchall()
        return list(reversed([dict(r) for r in rows]))
    finally:
        cur.close()
        conn.close()


def get_earliest_memories(user_id: str, limit: int = 5) -> list:
    """
    Fetch the OLDEST memories for a user — chronological order ascending.
    Used to answer "what was the first thing I told you" queries.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, role, message, importance_score, created_at
            FROM memories
            WHERE user_id = %s AND role = 'user'
            ORDER BY created_at ASC
            LIMIT %s;
            """,
            (user_id, limit)
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        cur.close()
        conn.close()


def search_memories_by_keyword(user_id: str, keyword: str, limit: int = 5) -> list:
    """
    Full-text keyword search across all memories.
    Fallback when FAISS semantic search doesn't find a match.
    Uses PostgreSQL ILIKE for case-insensitive substring match.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, role, message, importance_score, created_at
            FROM memories
            WHERE user_id = %s
              AND role = 'user'
              AND message ILIKE %s
            ORDER BY created_at ASC
            LIMIT %s;
            """,
            (user_id, f"%{keyword}%", limit)
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        cur.close()
        conn.close()


def get_chat_history(user_id: str, turns: int = 5) -> list:
    """
    Return last N conversation turns as (user_msg, bot_msg) pairs.
    Used to feed context back into the AI model.

    Args:
        user_id : unique user identifier
        turns   : number of past turns to retrieve

    Returns:
        List of tuples: [(user_msg, bot_msg), ...]
    """
    # Fetch enough messages to form complete turns
    memories = get_memories(user_id, limit=turns * 2)

    history = []
    i = 0
    while i < len(memories) - 1:
        if memories[i]["role"] == "user" and memories[i+1]["role"] == "assistant":
            history.append((memories[i]["message"], memories[i+1]["message"]))
            i += 2
        else:
            i += 1

    return history[-turns:]  # return only last N turns


def get_memory_count(user_id: str) -> int:
    """Return total number of memories stored for a user."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT COUNT(*) as count FROM memories WHERE user_id = %s;",
            (user_id,)
        )
        result = cur.fetchone()
        return result["count"] if result else 0
    finally:
        cur.close()
        conn.close()
