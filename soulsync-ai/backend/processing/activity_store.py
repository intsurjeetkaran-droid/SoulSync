"""
SoulSync AI - Activity Store
Saves and retrieves structured activity data from PostgreSQL.
"""

from backend.memory.database import get_connection, get_cursor


def save_activity(user_id: str, raw_text: str, extracted: dict) -> int:
    """
    Save extracted structured data to activities table.

    Returns the new activity ID.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO activities
                (user_id, raw_text, emotion, activity, status, productivity, summary)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                user_id,
                raw_text,
                extracted.get("emotion"),
                extracted.get("activity"),
                extracted.get("status"),
                extracted.get("productivity"),
                extracted.get("summary"),
            )
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"]
    finally:
        cur.close()
        conn.close()


def get_activities(user_id: str, limit: int = 20) -> list:
    """
    Fetch recent structured activities for a user.
    Returns list of activity dicts.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, user_id, raw_text, emotion, activity,
                   status, productivity, summary, created_at
            FROM activities
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """,
            (user_id, limit)
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        cur.close()
        conn.close()


def get_emotion_summary(user_id: str) -> dict:
    """
    Count emotions for a user — used by Suggestion Engine later.
    Returns: {"happy": 3, "tired": 5, ...}
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT emotion, COUNT(*) as count
            FROM activities
            WHERE user_id = %s AND emotion IS NOT NULL
            GROUP BY emotion
            ORDER BY count DESC;
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        return {r["emotion"]: r["count"] for r in rows}
    finally:
        cur.close()
        conn.close()
