"""
Backfill activities table for users who have memories but no activities.
Extracts emotion/activity/status from stored user messages.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

import psycopg2
from backend.memory.database import get_connection
from backend.processing.extractor import extract_memory
from backend.processing.activity_store import save_activity

# Users to backfill — add any user_id that has 0 activities
USERS_TO_BACKFILL = [
    "elena_1777021041",
    "david_1777021050",
    "fatima_1777021060",
    "jake_1777021070",
    "yuki_1777021081",
]

SAMPLE_SIZE = 80  # messages to extract per user (keep it fast)

def backfill(user_id: str):
    conn = get_connection()
    cur  = conn.cursor()

    # Check if already has enough activities
    cur.execute("SELECT COUNT(*) FROM activities WHERE user_id=%s", (user_id,))
    count = cur.fetchone()[0]
    if count >= 10:
        print(f"[{user_id}] Already has {count} activities — skipping")
        conn.close()
        return

    # Fetch older user messages (skip recent queries, get historical data)
    cur.execute("""
        SELECT message FROM memories
        WHERE user_id=%s AND role='user'
        AND LENGTH(message) > 30
        ORDER BY created_at ASC
        LIMIT %s
    """, (user_id, SAMPLE_SIZE))
    messages = [row[0] for row in cur.fetchall()]
    conn.close()

    print(f"[{user_id}] Extracting from {len(messages)} messages...")
    saved = 0
    for msg in messages:
        try:
            extracted = extract_memory(msg)
            if extracted.get("emotion") and extracted["emotion"] != "neutral":
                save_activity(user_id, msg, extracted)
                saved += 1
        except Exception as e:
            pass

    print(f"[{user_id}] Saved {saved} activities ✅")


if __name__ == "__main__":
    for uid in USERS_TO_BACKFILL:
        backfill(uid)
    print("\nDone! Refresh the Insights tab in the app.")
