"""
SoulSync AI - Monthly Summary Generator
Generates and stores compressed monthly summaries for fast recall.

A monthly summary contains:
  - List of experiences that month
  - List of achievements
  - Dominant emotion / mood trend
  - Key people mentioned
  - Full narrative paragraph (Groq-generated)

Used by the recall engine to answer "what happened in March 2026?"
without scanning hundreds of individual records.
"""

import json
import logging
from datetime import date
from typing import Optional

from backend.memory.database import get_connection, get_cursor
from backend.memory.collection_store import get_entries_in_month

logger = logging.getLogger("soulsync.monthly_summary")


# ── Get existing summary ──────────────────────────────────

def get_monthly_summary(user_id: str, year: int, month: int) -> Optional[dict]:
    """
    Retrieve a pre-built monthly summary.
    Returns None if not yet generated.
    """
    year_month = f"{year:04d}-{month:02d}"
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, year_month, experiences, achievements,
                   emotions_trend, key_people, tasks_completed,
                   dominant_mood, full_summary, created_at
            FROM monthly_summaries
            WHERE user_id = %s AND year_month = %s;
            """,
            (user_id, year_month)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        cur.close()
        conn.close()


# ── Build summary ─────────────────────────────────────────

def build_monthly_summary(user_id: str, year: int, month: int,
                           force_rebuild: bool = False) -> dict:
    """
    Build (or rebuild) the monthly summary for a given month.

    Steps:
      1. Check if summary already exists (skip if not force_rebuild)
      2. Pull all collection entries for that month
      3. Extract experiences, achievements, people, emotions
      4. Call Groq to generate a narrative paragraph
      5. Store in monthly_summaries table

    Returns:
        The summary dict
    """
    year_month = f"{year:04d}-{month:02d}"

    # Return cached if exists and not forcing rebuild
    if not force_rebuild:
        existing = get_monthly_summary(user_id, year, month)
        if existing:
            logger.info(f"[Monthly] Cache hit: {user_id} / {year_month}")
            return existing

    logger.info(f"[Monthly] Building summary: {user_id} / {year_month}")

    # Pull all entries for this month
    entries = get_entries_in_month(user_id, year, month)

    if not entries:
        logger.info(f"[Monthly] No data for {year_month}")
        return _store_empty_summary(user_id, year_month)

    # Extract by collection type
    experiences  = [e["content"] for e in entries if e["collection"] == "experience"]
    achievements = [e["content"] for e in entries if e["collection"] == "achievement"]
    emotions     = [e["content"] for e in entries if e["collection"] == "emotion_log"]
    relationships= [e["content"] for e in entries if e["collection"] == "relationship"]

    # Extract key people from relationship entries
    key_people = _extract_people(relationships)

    # Dominant mood from emotion entries
    dominant_mood, emotions_trend = _analyze_emotions(emotions)

    # Count tasks completed that month (from tasks table)
    tasks_completed = _count_tasks_completed(user_id, year, month)

    # Generate narrative with Groq
    full_summary = _generate_narrative(
        user_id, year_month, entries,
        experiences, achievements, emotions, key_people
    )

    # Store in DB
    result = _upsert_summary(
        user_id       = user_id,
        year_month    = year_month,
        experiences   = experiences[:10],   # cap at 10
        achievements  = achievements[:10],
        emotions_trend= emotions_trend,
        key_people    = key_people[:10],
        tasks_completed = tasks_completed,
        dominant_mood = dominant_mood,
        full_summary  = full_summary,
    )

    logger.info(f"[Monthly] Summary built: {year_month} | {len(entries)} entries")
    return result


def _extract_people(relationship_entries: list) -> list:
    """Extract unique person names from relationship entries."""
    import re
    people = set()
    name_pattern = re.compile(
        r"my (?:friend|mom|dad|mother|father|sister|brother|wife|husband|"
        r"partner|girlfriend|boyfriend|colleague|manager|boss|mentor|cousin|"
        r"aunt|uncle|grandma|grandpa)\s+(\w+)|"
        r"(?:called|texted|met|visited|talked to|spoke with|had dinner with) (\w+)",
        re.IGNORECASE
    )
    for entry in relationship_entries:
        for m in name_pattern.finditer(entry):
            name = m.group(1) or m.group(2)
            if name and len(name) > 2 and name.lower() not in {"the", "my", "a", "an"}:
                people.add(name.capitalize())
    return list(people)


def _analyze_emotions(emotion_entries: list) -> tuple:
    """Return (dominant_mood, trend_description) from emotion entries."""
    if not emotion_entries:
        return "neutral", "No strong emotions recorded this month."

    emotion_keywords = {
        "happy"    : ["happy", "joyful", "great", "amazing", "wonderful", "excited"],
        "stressed" : ["stressed", "overwhelmed", "anxious", "pressure", "tense"],
        "sad"      : ["sad", "down", "depressed", "unhappy", "miserable"],
        "motivated": ["motivated", "inspired", "energized", "focused", "productive"],
        "tired"    : ["tired", "exhausted", "drained", "fatigued"],
        "grateful" : ["grateful", "thankful", "blessed", "appreciative"],
    }

    counts = {k: 0 for k in emotion_keywords}
    text = " ".join(emotion_entries).lower()

    for emotion, keywords in emotion_keywords.items():
        for kw in keywords:
            counts[emotion] += text.count(kw)

    dominant = max(counts, key=counts.get) if any(counts.values()) else "neutral"
    trend = f"Predominantly {dominant} this month."
    return dominant, trend


def _count_tasks_completed(user_id: str, year: int, month: int) -> int:
    """Count tasks completed in a given month."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT COUNT(*) as c FROM tasks
            WHERE user_id = %s
              AND status = 'completed'
              AND EXTRACT(YEAR  FROM created_at) = %s
              AND EXTRACT(MONTH FROM created_at) = %s;
            """,
            (user_id, year, month)
        )
        return cur.fetchone()["c"]
    finally:
        cur.close()
        conn.close()


def _generate_narrative(user_id: str, year_month: str, entries: list,
                        experiences: list, achievements: list,
                        emotions: list, key_people: list) -> str:
    """
    Use Groq to generate a natural-language narrative summary of the month.
    Falls back to a structured summary if Groq fails.
    """
    try:
        from backend.core.ai_service import client, GROQ_MODEL

        # Build a compact data block for Groq
        data_lines = []
        for e in entries[:20]:   # cap at 20 to stay within token limit
            col  = e["collection"]
            date_str = str(e.get("event_date") or e["created_at"])[:10]
            data_lines.append(f"[{col}] ({date_str}) {e['content'][:120]}")

        data_block = "\n".join(data_lines)

        prompt = (
            f"You are summarizing a person's life for the month of {year_month}.\n"
            f"Here are their logged memories:\n\n{data_block}\n\n"
            f"Write a warm, personal 2-3 sentence narrative summary of this month "
            f"as if you are their AI companion recalling it. "
            f"Mention key events, emotions, and people. Be specific, not generic."
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a personal AI companion summarizing a user's month."},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=200,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.warning(f"[Monthly] Groq narrative failed: {e}")
        # Structured fallback
        parts = []
        if experiences:
            parts.append(f"Experiences: {'; '.join(experiences[:3])}")
        if achievements:
            parts.append(f"Achievements: {'; '.join(achievements[:3])}")
        if key_people:
            parts.append(f"Key people: {', '.join(key_people[:5])}")
        return f"{year_month}: " + ". ".join(parts) if parts else f"No significant events in {year_month}."


def _upsert_summary(user_id, year_month, experiences, achievements,
                    emotions_trend, key_people, tasks_completed,
                    dominant_mood, full_summary) -> dict:
    """Insert or update a monthly summary record."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO monthly_summaries
              (user_id, year_month, experiences, achievements, emotions_trend,
               key_people, tasks_completed, dominant_mood, full_summary, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, year_month)
            DO UPDATE SET
              experiences     = EXCLUDED.experiences,
              achievements    = EXCLUDED.achievements,
              emotions_trend  = EXCLUDED.emotions_trend,
              key_people      = EXCLUDED.key_people,
              tasks_completed = EXCLUDED.tasks_completed,
              dominant_mood   = EXCLUDED.dominant_mood,
              full_summary    = EXCLUDED.full_summary,
              updated_at      = NOW()
            RETURNING *;
            """,
            (
                user_id, year_month,
                json.dumps(experiences), json.dumps(achievements),
                emotions_trend, json.dumps(key_people),
                tasks_completed, dominant_mood, full_summary
            )
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)
    finally:
        cur.close()
        conn.close()


def _store_empty_summary(user_id: str, year_month: str) -> dict:
    return _upsert_summary(
        user_id, year_month, [], [], "No data", [], 0, "neutral",
        f"No memories recorded for {year_month}."
    )
