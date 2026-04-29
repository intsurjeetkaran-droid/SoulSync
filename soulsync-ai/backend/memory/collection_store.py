"""
SoulSync AI - Collection Store
Saves and queries typed memory collections.

Operations:
  save_to_collection       : classify + store a user message
  query_collection         : search within a specific collection
  get_collection_by_date   : find entries around a specific date
  get_earliest_in_collection : oldest entry in a collection
  get_conversation_chain   : messages within ±N days of a date
  keyword_search_collection: text search within a collection
"""

import logging
import json
from datetime import date, timedelta
from typing import Optional

from backend.memory.database import get_connection, get_cursor
from backend.processing.collection_classifier import classify_and_extract

logger = logging.getLogger("soulsync.collection_store")

# ── Save ──────────────────────────────────────────────────

def save_to_collection(user_id: str, text: str,
                       override_collection: str = None,
                       override_date: date = None) -> dict:
    """
    Classify a user message and save it to the appropriate collection.

    Args:
        user_id             : user identifier
        text                : raw user message
        override_collection : force a specific collection (skip classifier)
        override_date       : force a specific event_date

    Returns:
        dict with id, collection, event_date
    """
    meta = classify_and_extract(text)

    collection = override_collection or meta["collection"]
    event_date = override_date or meta["event_date"]
    importance = meta["importance"]

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO memory_collections
              (user_id, collection, content, event_date, importance)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, collection, event_date;
            """,
            (user_id, collection, text, event_date, importance)
        )
        row = cur.fetchone()
        conn.commit()
        result = dict(row)
        logger.info(
            f"[Collection] Saved: user={user_id} | "
            f"collection={collection} | date={event_date} | "
            f"text='{text[:50]}'"
        )
        return result
    except Exception as e:
        conn.rollback()
        logger.error(f"[Collection] Save failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ── Query by collection ───────────────────────────────────

def query_collection(user_id: str, collection: str,
                     limit: int = 10,
                     order: str = "DESC") -> list:
    """
    Fetch entries from a specific collection, ordered by event_date or created_at.

    Args:
        user_id    : user identifier
        collection : collection name
        limit      : max results
        order      : 'ASC' (oldest first) or 'DESC' (newest first)

    Returns:
        List of dicts
    """
    order = "ASC" if order.upper() == "ASC" else "DESC"
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            f"""
            SELECT id, collection, content, event_date, importance, created_at
            FROM memory_collections
            WHERE user_id = %s AND collection = %s
            ORDER BY COALESCE(event_date, created_at::date) {order}, created_at {order}
            LIMIT %s;
            """,
            (user_id, collection, limit)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_earliest_in_collection(user_id: str, collection: str) -> Optional[dict]:
    """Return the oldest entry in a collection."""
    results = query_collection(user_id, collection, limit=1, order="ASC")
    return results[0] if results else None


def get_all_collections_summary(user_id: str) -> dict:
    """
    Return count of entries per collection for a user.
    Used for 'tell me about me' overview.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT collection, COUNT(*) as count
            FROM memory_collections
            WHERE user_id = %s
            GROUP BY collection
            ORDER BY count DESC;
            """,
            (user_id,)
        )
        return {r["collection"]: r["count"] for r in cur.fetchall()}
    finally:
        cur.close()
        conn.close()


# ── Date-based queries ────────────────────────────────────

def get_conversation_chain(user_id: str, anchor_date: date,
                           window_days: int = 3) -> list:
    """
    Fetch all collection entries within ±window_days of anchor_date.
    Used to build context around a specific event for summarization.

    Returns:
        List of dicts ordered by date ASC
    """
    start = anchor_date - timedelta(days=window_days)
    end   = anchor_date + timedelta(days=window_days)

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, collection, content, event_date, created_at
            FROM memory_collections
            WHERE user_id = %s
              AND COALESCE(event_date, created_at::date) BETWEEN %s AND %s
            ORDER BY COALESCE(event_date, created_at::date) ASC, created_at ASC;
            """,
            (user_id, start, end)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_entries_in_month(user_id: str, year: int, month: int,
                         collection: str = None) -> list:
    """
    Fetch all entries for a specific year-month.
    Optionally filter by collection.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        if collection:
            cur.execute(
                """
                SELECT id, collection, content, event_date, importance, created_at
                FROM memory_collections
                WHERE user_id = %s
                  AND collection = %s
                  AND EXTRACT(YEAR  FROM COALESCE(event_date, created_at::date)) = %s
                  AND EXTRACT(MONTH FROM COALESCE(event_date, created_at::date)) = %s
                ORDER BY COALESCE(event_date, created_at::date) ASC;
                """,
                (user_id, collection, year, month)
            )
        else:
            cur.execute(
                """
                SELECT id, collection, content, event_date, importance, created_at
                FROM memory_collections
                WHERE user_id = %s
                  AND EXTRACT(YEAR  FROM COALESCE(event_date, created_at::date)) = %s
                  AND EXTRACT(MONTH FROM COALESCE(event_date, created_at::date)) = %s
                ORDER BY COALESCE(event_date, created_at::date) ASC;
                """,
                (user_id, year, month)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


# ── Keyword search ────────────────────────────────────────

def keyword_search_collection(user_id: str, keyword: str,
                               collection: str = None,
                               limit: int = 5) -> list:
    """
    Full-text keyword search within collections.
    Optionally scoped to a specific collection.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        if collection:
            cur.execute(
                """
                SELECT id, collection, content, event_date, created_at
                FROM memory_collections
                WHERE user_id = %s
                  AND collection = %s
                  AND content ILIKE %s
                ORDER BY COALESCE(event_date, created_at::date) ASC
                LIMIT %s;
                """,
                (user_id, collection, f"%{keyword}%", limit)
            )
        else:
            cur.execute(
                """
                SELECT id, collection, content, event_date, created_at
                FROM memory_collections
                WHERE user_id = %s
                  AND content ILIKE %s
                ORDER BY COALESCE(event_date, created_at::date) ASC
                LIMIT %s;
                """,
                (user_id, f"%{keyword}%", limit)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
