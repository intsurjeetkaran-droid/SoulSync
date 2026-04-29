"""
SoulSync AI - Life Timeline
Chronological diary of the user's life — day-wise with date and time.

Every significant message gets a timeline entry with:
  - entry_date / entry_time  : when the event happened
  - collection_type          : what kind of event (experience/emotion/etc.)
  - significance             : 1-10 importance score
  - tags                     : searchable labels
  - people_involved          : who was there
  - location                 : where it happened
  - mood_at_time             : emotional state at the moment

Day summaries are auto-generated and cached in life_timeline_days.
"""

import re
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from backend.memory.database import get_connection, get_cursor

logger = logging.getLogger("soulsync.life_timeline")

# ── Significance scoring ───────────────────────────────────
BASE_SIGNIFICANCE = {
    "achievement"     : 9,
    "experience"      : 8,
    "decision"        : 8,
    "conflict"        : 7,
    "reflection"      : 7,
    "goal"            : 7,
    "social_event"    : 6,
    "relationship"    : 6,
    "creative_work"   : 6,
    "future_plan"     : 5,
    "emotion_log"     : 5,
    "health"          : 5,
    "habit"           : 5,
    "financial"       : 5,
    "learning"        : 5,
    "gratitude"       : 5,
    "dream_aspiration": 4,
    "opinion"         : 4,
    "conversation"    : 2,
}

# Boost keywords that raise significance
SIGNIFICANCE_BOOST = {
    "first time"   : 2, "never before": 2, "life-changing": 3,
    "milestone"    : 2, "finally"     : 1, "biggest"      : 2,
    "most important": 2,"changed my life": 3, "unforgettable": 2,
    "proud"        : 1, "breakthrough": 2, "turning point": 3,
}


def _calc_significance(text: str, collection_type: str) -> int:
    """Calculate significance score 1-10 for a timeline entry."""
    base  = BASE_SIGNIFICANCE.get(collection_type, 5)
    boost = 0
    text_lower = text.lower()
    for phrase, pts in SIGNIFICANCE_BOOST.items():
        if phrase in text_lower:
            boost += pts
    return min(10, base + boost)


def _extract_people(text: str) -> list:
    """Extract names of people mentioned in the text."""
    # Match "my <relation> <Name>" or standalone capitalized names after verbs
    people = set()
    relation_pattern = re.compile(
        r"my (?:friend|mom|dad|mother|father|sister|brother|wife|husband|"
        r"partner|girlfriend|boyfriend|colleague|manager|boss|mentor|cousin|"
        r"aunt|uncle|grandma|grandpa)\s+([A-Z][a-z]+)",
        re.IGNORECASE
    )
    for m in relation_pattern.finditer(text):
        people.add(m.group(1).capitalize())

    # Also catch "with <Name>" patterns
    with_pattern = re.compile(r"\bwith\s+([A-Z][a-z]+)\b")
    for m in with_pattern.finditer(text):
        name = m.group(1)
        if name not in {"The", "My", "A", "An", "This", "That"}:
            people.add(name)

    return list(people)[:5]   # cap at 5


def _extract_location(text: str) -> Optional[str]:
    """Extract location from text if mentioned."""
    patterns = [
        r"(?:in|at|to|from|visited?|traveled? to|went to)\s+([A-Z][a-zA-Z\s,]+?)(?:\s+(?:for|and|but|,|\.|$))",
        r"(?:trip to|journey to|visit to)\s+([A-Z][a-zA-Z\s]+)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            loc = m.group(1).strip().rstrip(",.")
            if len(loc) > 2 and len(loc) < 50:
                return loc
    return None


def _extract_tags(text: str, collection_type: str) -> list:
    """Generate searchable tags from text and collection type."""
    tags = [collection_type]
    text_lower = text.lower()

    tag_keywords = {
        "travel": ["travel", "trip", "journey", "vacation", "holiday", "visited"],
        "work"  : ["work", "job", "office", "meeting", "project", "deadline"],
        "family": ["mom", "dad", "sister", "brother", "family", "parents"],
        "health": ["gym", "workout", "sick", "doctor", "sleep", "diet"],
        "social": ["party", "friends", "dinner", "celebration", "hangout"],
        "growth": ["learned", "realized", "improved", "achieved", "milestone"],
        "emotion": ["happy", "sad", "stressed", "excited", "anxious", "proud"],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)

    return list(set(tags))[:8]


def _extract_mood(text: str) -> Optional[str]:
    """Extract the dominant mood from text."""
    mood_words = {
        "happy"    : ["happy", "joyful", "excited", "great", "amazing", "wonderful"],
        "sad"      : ["sad", "unhappy", "depressed", "down", "miserable"],
        "stressed" : ["stressed", "anxious", "overwhelmed", "nervous", "worried"],
        "angry"    : ["angry", "frustrated", "annoyed", "furious", "mad"],
        "tired"    : ["tired", "exhausted", "drained", "fatigued", "sleepy"],
        "motivated": ["motivated", "inspired", "energized", "focused", "pumped"],
        "grateful" : ["grateful", "thankful", "blessed", "appreciative"],
        "proud"    : ["proud", "accomplished", "achieved", "succeeded"],
        "scared"   : ["scared", "afraid", "terrified", "nervous", "fearful"],
        "content"  : ["content", "peaceful", "calm", "relaxed", "satisfied"],
    }
    text_lower = text.lower()
    for mood, keywords in mood_words.items():
        if any(kw in text_lower for kw in keywords):
            return mood
    return None


# ── Save to timeline ──────────────────────────────────────

def add_to_timeline(user_id: str, content: str,
                    collection_type: str,
                    event_date: Optional[date] = None,
                    event_time: Optional[str] = None,
                    source: str = "chat") -> Optional[dict]:
    """
    Add an entry to the user's life timeline.

    Args:
        user_id         : user identifier
        content         : the message/event text
        collection_type : which collection this belongs to
        event_date      : actual date of the event (defaults to today)
        event_time      : time string "HH:MM" (optional)
        source          : "chat" | "voice" | "manual"

    Returns:
        dict with the created timeline entry, or None if skipped
    """
    # Skip conversation fallback — not significant enough for timeline
    if collection_type == "conversation":
        return None

    today      = date.today()
    entry_date = event_date or today
    now        = datetime.now()

    # Build entry_datetime from date + time
    if event_time:
        try:
            h, m = map(int, event_time.split(":"))
            entry_datetime = datetime(entry_date.year, entry_date.month,
                                      entry_date.day, h, m)
        except Exception:
            entry_datetime = now
    else:
        entry_datetime = datetime(entry_date.year, entry_date.month,
                                  entry_date.day, now.hour, now.minute, now.second)

    significance    = _calc_significance(content, collection_type)
    people_involved = _extract_people(content)
    location        = _extract_location(content)
    tags            = _extract_tags(content, collection_type)
    mood            = _extract_mood(content)

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO life_timeline
              (user_id, entry_date, entry_time, entry_datetime, content,
               collection_type, significance, tags, people_involved,
               location, mood_at_time, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, entry_date, entry_datetime, collection_type,
                      significance, mood_at_time, location;
            """,
            (
                user_id, entry_date,
                event_time,
                entry_datetime,
                content,
                collection_type,
                significance,
                json.dumps(tags),
                json.dumps(people_involved),
                location,
                mood,
                source,
            )
        )
        row = cur.fetchone()
        conn.commit()
        result = dict(row)
        logger.info(
            f"[Timeline] Added: user={user_id} | date={entry_date} | "
            f"type={collection_type} | sig={significance} | "
            f"mood={mood} | loc={location}"
        )

        # Invalidate day summary so it gets rebuilt next time
        _invalidate_day_summary(cur, conn, user_id, entry_date)

        return result

    except Exception as e:
        conn.rollback()
        logger.error(f"[Timeline] Add failed: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def _invalidate_day_summary(cur, conn, user_id: str, day: date):
    """Mark day summary as stale by deleting it (will be rebuilt on next query)."""
    try:
        cur.execute(
            "DELETE FROM life_timeline_days WHERE user_id = %s AND day_date = %s",
            (user_id, day)
        )
        conn.commit()
    except Exception:
        pass


# ── Query timeline ────────────────────────────────────────

def get_timeline_for_date(user_id: str, target_date: date) -> list:
    """Get all timeline entries for a specific date, ordered by time."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, entry_date, entry_time, entry_datetime, content,
                   collection_type, significance, tags, people_involved,
                   location, mood_at_time, source, created_at
            FROM life_timeline
            WHERE user_id = %s AND entry_date = %s
            ORDER BY entry_datetime ASC;
            """,
            (user_id, target_date)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_timeline_range(user_id: str, start: date, end: date,
                       collection_type: str = None,
                       min_significance: int = 1) -> list:
    """Get timeline entries within a date range."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        if collection_type:
            cur.execute(
                """
                SELECT id, entry_date, entry_datetime, content,
                       collection_type, significance, mood_at_time, location
                FROM life_timeline
                WHERE user_id = %s
                  AND entry_date BETWEEN %s AND %s
                  AND collection_type = %s
                  AND significance >= %s
                ORDER BY entry_datetime ASC;
                """,
                (user_id, start, end, collection_type, min_significance)
            )
        else:
            cur.execute(
                """
                SELECT id, entry_date, entry_datetime, content,
                       collection_type, significance, mood_at_time, location
                FROM life_timeline
                WHERE user_id = %s
                  AND entry_date BETWEEN %s AND %s
                  AND significance >= %s
                ORDER BY entry_datetime ASC;
                """,
                (user_id, start, end, min_significance)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_most_significant_moments(user_id: str, limit: int = 10,
                                  min_significance: int = 7) -> list:
    """Return the most significant moments in the user's life."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, entry_date, entry_datetime, content,
                   collection_type, significance, mood_at_time, location
            FROM life_timeline
            WHERE user_id = %s AND significance >= %s
            ORDER BY significance DESC, entry_date DESC
            LIMIT %s;
            """,
            (user_id, min_significance, limit)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_timeline_by_mood(user_id: str, mood: str, limit: int = 10) -> list:
    """Find all moments when the user felt a specific mood."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, entry_date, entry_datetime, content,
                   collection_type, significance, mood_at_time, location
            FROM life_timeline
            WHERE user_id = %s AND mood_at_time = %s
            ORDER BY entry_date DESC
            LIMIT %s;
            """,
            (user_id, mood, limit)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_timeline_by_person(user_id: str, person_name: str, limit: int = 10) -> list:
    """Find all moments involving a specific person."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, entry_date, entry_datetime, content,
                   collection_type, significance, mood_at_time, location
            FROM life_timeline
            WHERE user_id = %s
              AND people_involved::text ILIKE %s
            ORDER BY entry_date DESC
            LIMIT %s;
            """,
            (user_id, f"%{person_name}%", limit)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_timeline_by_location(user_id: str, location: str, limit: int = 10) -> list:
    """Find all moments at a specific location."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, entry_date, entry_datetime, content,
                   collection_type, significance, mood_at_time, location
            FROM life_timeline
            WHERE user_id = %s AND location ILIKE %s
            ORDER BY entry_date DESC
            LIMIT %s;
            """,
            (user_id, f"%{location}%", limit)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def search_timeline(user_id: str, keyword: str, limit: int = 10) -> list:
    """Full-text search across timeline content."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, entry_date, entry_datetime, content,
                   collection_type, significance, mood_at_time, location
            FROM life_timeline
            WHERE user_id = %s AND content ILIKE %s
            ORDER BY significance DESC, entry_date DESC
            LIMIT %s;
            """,
            (user_id, f"%{keyword}%", limit)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


# ── Day summary ───────────────────────────────────────────

def get_day_summary(user_id: str, target_date: date,
                    force_rebuild: bool = False) -> dict:
    """
    Get or build the day summary for a specific date.

    Returns a dict with summary, dominant_emotion, significance,
    entry_count, key_events, people, locations.
    """
    conn = get_connection()
    cur  = get_cursor(conn)

    # Check cache
    if not force_rebuild:
        try:
            cur.execute(
                """
                SELECT * FROM life_timeline_days
                WHERE user_id = %s AND day_date = %s;
                """,
                (user_id, target_date)
            )
            row = cur.fetchone()
            if row:
                return dict(row)
        except Exception:
            pass
        finally:
            cur.close()
            conn.close()

    # Build from raw entries
    entries = get_timeline_for_date(user_id, target_date)
    if not entries:
        return {
            "day_date"          : str(target_date),
            "summary"           : f"No events recorded for {target_date}.",
            "dominant_emotion"  : None,
            "significance"      : 0.0,
            "entry_count"       : 0,
            "collections_touched": [],
            "key_events"        : [],
            "people"            : [],
            "locations"         : [],
        }

    # Aggregate metadata
    all_moods       = [e["mood_at_time"] for e in entries if e.get("mood_at_time")]
    all_collections = list(set(e["collection_type"] for e in entries))
    all_people      = list(set(
        p for e in entries
        for p in (json.loads(e["people_involved"]) if isinstance(e["people_involved"], str)
                  else (e["people_involved"] or []))
    ))
    all_locations   = list(set(e["location"] for e in entries if e.get("location")))
    avg_significance = round(sum(e["significance"] for e in entries) / len(entries), 1)

    # Dominant mood
    dominant_mood = None
    if all_moods:
        from collections import Counter
        dominant_mood = Counter(all_moods).most_common(1)[0][0]

    # Key events = highest significance entries
    key_events = sorted(entries, key=lambda x: x["significance"], reverse=True)[:3]
    key_event_texts = [e["content"][:100] for e in key_events]

    # Generate narrative with Groq
    summary_text = _generate_day_narrative(
        target_date, entries, dominant_mood, all_people, all_locations
    )

    # Store in cache
    result = _upsert_day_summary(
        user_id          = user_id,
        day_date         = target_date,
        summary          = summary_text,
        dominant_emotion = dominant_mood,
        significance     = avg_significance,
        entry_count      = len(entries),
        collections      = all_collections,
        key_events       = key_event_texts,
        people           = all_people[:10],
        locations        = all_locations[:5],
    )
    return result


def _generate_day_narrative(target_date: date, entries: list,
                             dominant_mood: Optional[str],
                             people: list, locations: list) -> str:
    """Use Groq to write a 1-2 sentence narrative for the day."""
    try:
        from backend.core.ai_service import client, GROQ_MODEL

        lines = []
        for e in entries[:8]:
            t = str(e.get("entry_datetime", ""))[:16]
            lines.append(f"[{e['collection_type']}] {t} — {e['content'][:100]}")

        data = "\n".join(lines)
        mood_str    = f"Dominant mood: {dominant_mood}. " if dominant_mood else ""
        people_str  = f"People: {', '.join(people[:3])}. " if people else ""
        loc_str     = f"Locations: {', '.join(locations[:2])}. " if locations else ""

        prompt = (
            f"Write a warm 1-2 sentence diary entry for {target_date}.\n"
            f"{mood_str}{people_str}{loc_str}\n"
            f"Events:\n{data}\n\n"
            f"Be specific and personal. Write as if recalling this day for the user."
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a personal AI writing a diary summary."},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=150,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.warning(f"[Timeline] Day narrative failed: {e}")
        # Structured fallback
        parts = [f"{len(entries)} event(s) recorded"]
        if dominant_mood:
            parts.append(f"mood: {dominant_mood}")
        if locations:
            parts.append(f"location: {locations[0]}")
        return f"{target_date}: " + ", ".join(parts) + "."


def _upsert_day_summary(user_id, day_date, summary, dominant_emotion,
                        significance, entry_count, collections,
                        key_events, people, locations) -> dict:
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO life_timeline_days
              (user_id, day_date, summary, dominant_emotion, significance,
               entry_count, collections_touched, key_events, people, locations,
               updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, day_date)
            DO UPDATE SET
              summary             = EXCLUDED.summary,
              dominant_emotion    = EXCLUDED.dominant_emotion,
              significance        = EXCLUDED.significance,
              entry_count         = EXCLUDED.entry_count,
              collections_touched = EXCLUDED.collections_touched,
              key_events          = EXCLUDED.key_events,
              people              = EXCLUDED.people,
              locations           = EXCLUDED.locations,
              updated_at          = NOW()
            RETURNING *;
            """,
            (
                user_id, day_date, summary, dominant_emotion, significance,
                entry_count,
                json.dumps(collections),
                json.dumps(key_events),
                json.dumps(people),
                json.dumps(locations),
            )
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)
    finally:
        cur.close()
        conn.close()


# ── Week / period summaries ───────────────────────────────

def get_week_summary(user_id: str, reference_date: date = None) -> dict:
    """Get a summary of the last 7 days."""
    end   = reference_date or date.today()
    start = end - timedelta(days=6)
    entries = get_timeline_range(user_id, start, end, min_significance=3)

    if not entries:
        return {
            "period"  : f"{start} to {end}",
            "found"   : False,
            "summary" : "No significant events in the last 7 days.",
            "entries" : [],
        }

    # Group by day
    by_day = {}
    for e in entries:
        d = str(e["entry_date"])
        if d not in by_day:
            by_day[d] = []
        by_day[d].append(e["content"][:80])

    lines = []
    for d in sorted(by_day.keys()):
        lines.append(f"  {d}: " + " | ".join(by_day[d][:2]))

    return {
        "period"  : f"{start} to {end}",
        "found"   : True,
        "summary" : "\n".join(lines),
        "entries" : entries,
    }


def get_life_story(user_id: str, limit_days: int = 30) -> list:
    """
    Return day summaries for the last N days — the user's life story.
    """
    end   = date.today()
    start = end - timedelta(days=limit_days)

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT day_date, summary, dominant_emotion, significance,
                   entry_count, key_events, people, locations
            FROM life_timeline_days
            WHERE user_id = %s AND day_date BETWEEN %s AND %s
            ORDER BY day_date ASC;
            """,
            (user_id, start, end)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
