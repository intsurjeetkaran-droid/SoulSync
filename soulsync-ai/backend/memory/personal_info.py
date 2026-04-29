"""
SoulSync AI - Personal Info Manager
Handles structured key/value personal facts with full timestamp support.

Every fact now stores:
  - created_at  : when the fact was first recorded
  - updated_at  : when it was last changed
  - event_date  : the actual date the fact refers to
                  e.g. "My goal is X" → event_date = today
                       "My birthday is March 15" → event_date = March 15
  - context     : category hint (goal / birthday / preference / identity)

This enables queries like:
  "What was my goal in January?"
  "What goals have I set this year?"
  "When did I last update my job info?"
"""

import logging
import time as _time
from datetime import date
from typing import Optional
from backend.memory.database import get_connection, get_cursor

logger = logging.getLogger("soulsync.personal_info")

# ─── Key → context category mapping ──────────────────────
KEY_CONTEXT = {
    "name"     : "identity",
    "age"      : "identity",
    "email"    : "identity",
    "phone"    : "identity",
    "location" : "identity",
    "job"      : "career",
    "goal"     : "goal",
    "dream"    : "goal",
    "aim"      : "goal",
    "hobby"    : "preference",
    "interest" : "preference",
}

# ─── Human-readable labels ────────────────────────────────
KEY_LABELS = {
    "name"     : "Name",
    "age"      : "Age",
    "goal"     : "Goal",
    "dream"    : "Dream",
    "aim"      : "Aim",
    "job"      : "Job / Profession",
    "hobby"    : "Hobby",
    "interest" : "Interest",
    "location" : "Location",
    "email"    : "Email",
    "phone"    : "Phone",
}

# Keys that should APPEND (multiple values allowed) vs UPSERT (single value)
APPENDABLE_KEYS = {"goal", "dream", "aim", "opinion", "interest"}


# ─── Store ────────────────────────────────────────────────

def store_personal_info(user_id: str, key: str, value: str,
                        source_text: str = None,
                        event_date: date = None) -> dict:
    """
    Store a personal info fact with full timestamp metadata.

    - Appendable keys (goal, dream, opinion, interest) → always INSERT new row
      with a timestamped unique key so history is preserved.
    - Other keys (name, job, location, etc.) → UPSERT (update if exists).

    event_date defaults to today for goals/dreams (when they were set).
    """
    key_lower = key.lower()
    context   = KEY_CONTEXT.get(key_lower, "general")

    # Default event_date to today for time-sensitive keys
    if event_date is None and key_lower in APPENDABLE_KEYS:
        event_date = date.today()

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        if key_lower in APPENDABLE_KEYS or key_lower.startswith("opinion_"):
            # Append — unique key per entry preserves full history
            unique_key = f"{key_lower}_{int(_time.time() * 1000) % 1000000}"
            cur.execute(
                """
                INSERT INTO personal_info
                  (user_id, key, value, source_text, context, event_date, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id, user_id, key, value, context, event_date,
                          created_at, updated_at;
                """,
                (user_id, unique_key, value, source_text, context, event_date)
            )
        else:
            # Upsert — single canonical value per key
            cur.execute(
                """
                INSERT INTO personal_info
                  (user_id, key, value, source_text, context, event_date, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id, key)
                DO UPDATE SET
                    value       = EXCLUDED.value,
                    source_text = EXCLUDED.source_text,
                    context     = EXCLUDED.context,
                    event_date  = COALESCE(EXCLUDED.event_date, personal_info.event_date),
                    updated_at  = NOW()
                RETURNING id, user_id, key, value, context, event_date,
                          created_at, updated_at;
                """,
                (user_id, key_lower, value, source_text, context, event_date)
            )

        row = cur.fetchone()
        conn.commit()
        result = dict(row)
        logger.info(
            f"[PersonalInfo] Stored: user={user_id} | key={key_lower} | "
            f"value={value[:40]} | event_date={event_date}"
        )
        return result

    except Exception as e:
        conn.rollback()
        logger.error(f"[PersonalInfo] Store failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ─── Retrieve ─────────────────────────────────────────────

def get_personal_info(user_id: str, key: str = None,
                      context: str = None) -> list:
    """
    Retrieve personal info for a user.

    Args:
        user_id : user identifier
        key     : specific key prefix (None = all)
        context : filter by context category (goal/identity/preference/career)

    Returns:
        List of dicts with key, value, context, event_date, created_at, updated_at
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        if key and context:
            cur.execute(
                """
                SELECT key, value, context, event_date, created_at, updated_at
                FROM personal_info
                WHERE user_id = %s AND key LIKE %s AND context = %s
                ORDER BY COALESCE(event_date, created_at::date) DESC;
                """,
                (user_id, f"{key.lower()}%", context)
            )
        elif key:
            cur.execute(
                """
                SELECT key, value, context, event_date, created_at, updated_at
                FROM personal_info
                WHERE user_id = %s AND key LIKE %s
                ORDER BY COALESCE(event_date, created_at::date) DESC;
                """,
                (user_id, f"{key.lower()}%")
            )
        elif context:
            cur.execute(
                """
                SELECT key, value, context, event_date, created_at, updated_at
                FROM personal_info
                WHERE user_id = %s AND context = %s
                ORDER BY COALESCE(event_date, created_at::date) DESC;
                """,
                (user_id, context)
            )
        else:
            cur.execute(
                """
                SELECT key, value, context, event_date, created_at, updated_at
                FROM personal_info
                WHERE user_id = %s
                ORDER BY context ASC, COALESCE(event_date, created_at::date) DESC;
                """,
                (user_id,)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_single_value(user_id: str, key: str) -> Optional[str]:
    """Get the most recent value for a key. Returns None if not found."""
    rows = get_personal_info(user_id, key)
    return rows[0]["value"] if rows else None


def get_goals_timeline(user_id: str) -> list:
    """
    Return all goals with their dates — for timeline recall.
    e.g. "What goals have I set this year?"
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT key, value, event_date, created_at, updated_at
            FROM personal_info
            WHERE user_id = %s AND context = 'goal'
            ORDER BY COALESCE(event_date, created_at::date) ASC;
            """,
            (user_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_facts_in_period(user_id: str, start: date, end: date,
                        context: str = None) -> list:
    """
    Retrieve facts set/updated within a date range.
    Useful for: "What were my goals in January?"
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        if context:
            cur.execute(
                """
                SELECT key, value, context, event_date, created_at, updated_at
                FROM personal_info
                WHERE user_id = %s
                  AND context = %s
                  AND COALESCE(event_date, created_at::date) BETWEEN %s AND %s
                ORDER BY COALESCE(event_date, created_at::date) ASC;
                """,
                (user_id, context, start, end)
            )
        else:
            cur.execute(
                """
                SELECT key, value, context, event_date, created_at, updated_at
                FROM personal_info
                WHERE user_id = %s
                  AND COALESCE(event_date, created_at::date) BETWEEN %s AND %s
                ORDER BY COALESCE(event_date, created_at::date) ASC;
                """,
                (user_id, start, end)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


# ─── Format for Prompt ────────────────────────────────────

def format_for_prompt(user_id: str) -> str:
    """
    Format all personal info as a readable context block for the AI prompt.
    Groups by context category. Includes dates for goals/dreams.
    """
    facts = get_personal_info(user_id)
    if not facts:
        return ""

    # Group by context
    groups = {}
    for f in facts:
        ctx = f.get("context") or "general"
        if ctx not in groups:
            groups[ctx] = []
        groups[ctx].append(f)

    lines = []
    ctx_order = ["identity", "career", "goal", "preference", "general"]

    for ctx in ctx_order:
        if ctx not in groups:
            continue
        for f in groups[ctx]:
            raw_key = f["key"].split("_")[0]   # strip timestamp suffix
            label   = KEY_LABELS.get(raw_key, raw_key.replace("_", " ").title())
            date_str = ""
            if f.get("event_date"):
                date_str = f" (set {str(f['event_date'])[:10]})"
            elif f.get("updated_at"):
                date_str = f" (updated {str(f['updated_at'])[:10]})"
            lines.append(f"- {label}: {f['value']}{date_str}")

    return "Known facts about this user:\n" + "\n".join(lines)


# ─── Direct Answer Builder ────────────────────────────────

def build_direct_answer(user_id: str, query_key: Optional[str]) -> Optional[str]:
    """
    Return a direct answer from DB without calling the AI.
    Handles: specific keys, all-facts, chronological, goals timeline.
    """

    # ── Chronological / first-experience ──────────────────
    if query_key == "__earliest__":
        from backend.memory.memory_manager import get_earliest_memories
        earliest = get_earliest_memories(user_id, limit=3)
        if not earliest:
            return None
        lines = []
        for m in earliest:
            ts = str(m["created_at"])[:10]
            lines.append(f'• [{ts}] "{m["message"]}"')
        return (
            "Here are the earliest things you shared with me:\n"
            + "\n".join(lines)
            + "\n\nThese are your first memories in SoulSync. 🧠"
        )

    # ── All facts ─────────────────────────────────────────
    if query_key is None:
        facts = get_personal_info(user_id)
        if not facts:
            return None
        lines = []
        for f in facts:
            raw_key  = f["key"].split("_")[0]
            label    = KEY_LABELS.get(raw_key, raw_key.replace("_", " ").title())
            date_str = f" [{str(f['event_date'])[:10]}]" if f.get("event_date") else ""
            lines.append(f"• {label}: {f['value']}{date_str}")
        return "Here's what I know about you:\n" + "\n".join(lines) + " 😊"

    # ── Goals timeline ────────────────────────────────────
    if query_key == "goal":
        goals = get_goals_timeline(user_id)
        if not goals:
            return None
        if len(goals) == 1:
            g = goals[0]
            date_str = f" (set on {str(g['event_date'])[:10]})" if g.get("event_date") else ""
            return f"Your goal is: {g['value']}{date_str} 💪"
        # Multiple goals — show timeline
        lines = []
        for g in goals:
            date_str = str(g.get("event_date") or g["created_at"])[:10]
            lines.append(f"• [{date_str}] {g['value']}")
        return "Your goals over time:\n" + "\n".join(lines) + " 💪"

    # ── Specific key lookup ───────────────────────────────
    rows = get_personal_info(user_id, query_key)
    if not rows:
        return None

    f     = rows[0]
    value = f["value"]
    label = KEY_LABELS.get(query_key, query_key.replace("_", " ").title())

    # Add date context for time-sensitive facts
    date_str = ""
    if f.get("event_date"):
        date_str = f" (as of {str(f['event_date'])[:10]})"
    elif f.get("updated_at"):
        date_str = f" (last updated {str(f['updated_at'])[:10]})"

    answers = {
        "name"    : f"Your name is {value} 😊",
        "age"     : f"You are {value} years old{date_str}.",
        "goal"    : f"Your goal is: {value}{date_str} 💪",
        "dream"   : f"Your dream is: {value}{date_str} ✨",
        "aim"     : f"Your aim is: {value}{date_str}",
        "job"     : f"You work as: {value}{date_str}",
        "hobby"   : f"Your hobby is: {value}",
        "interest": f"You enjoy: {value}",
        "location": f"You live in {value}{date_str}.",
        "email"   : f"Your email is {value}.",
        "phone"   : f"Your phone number is {value}.",
    }

    if query_key in answers:
        return answers[query_key]

    return f"Your {label.lower()} is: {value}{date_str}"
