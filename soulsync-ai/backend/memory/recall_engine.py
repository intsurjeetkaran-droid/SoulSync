"""
SoulSync AI - Recall Engine
Smart routing for memory recall queries.

Routes:
  CHRONOLOGICAL  → "first experience", "earliest memory"
                   → experience collection ORDER BY event_date ASC
  MONTHLY        → "what happened in March 2026"
                   → monthly_summaries direct lookup
  COLLECTION     → "tell me about my Jammu trip", "my achievements"
                   → typed collection keyword search + chain summarizer
  EMOTION_PERIOD → "how was I feeling in November"
                   → emotion_log collection date range
  GENERAL        → everything else
                   → FAISS + keyword fallback (existing system)
"""

import re
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("soulsync.recall_engine")

MONTH_MAP = {
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12
}

# ── Recall intent patterns ────────────────────────────────

CHRONOLOGICAL_PATTERNS = [
    r"(?:first|earliest|oldest) (?:experience|memory|thing|event|story|message)",
    r"what (?:was|were|is) (?:the )?first (?:thing|experience|event|memory)",
    r"what did i (?:first|initially) (?:tell|share|say|mention)",
    r"what was my first",
    r"recall (?:my )?first",
    r"do you remember (?:the )?first",
]

MONTHLY_PATTERNS = [
    r"what happened (?:in|during|on) (january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(\d{4}))?",
    r"(?:tell me about|summarize|recap) (january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(\d{4}))?",
    r"(?:in|during) (january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(\d{4}))? (?:what|how|did)",
    r"(january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(\d{4}))? (?:summary|recap|review)",
]

# ── Timeline-specific patterns (day/week/period) ──────────
TIMELINE_PATTERNS = [
    r"what happened (?:on|yesterday|today|last (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))",
    r"(?:tell me about|walk me through|recap) (?:my|last) (?:week|day|weekend)",
    r"what was i doing (?:on|last|this) (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|week)",
    r"(?:my|show me my) (?:life story|timeline|history)",
    r"(?:show me|what are|list) (?:my )?(?:most )?(?:significant|important) (?:moments?|days?|events?)",
    r"when (?:did i last|was the last time i) feel (?:happy|sad|stressed|excited|proud)",
    r"(?:all|every) (?:time|moment) (?:i|with) (?:felt|was with|mentioned|went to)",
    r"what happened (?:on )?\d{4}-\d{2}-\d{2}",
]

COLLECTION_RECALL_PATTERNS = {
    "experience"      : [r"(?:my|tell me about my|recall my) (?:trip|travel|visit|experience|journey|vacation)"],
    "achievement"     : [r"(?:my|what are my|list my) (?:achievements?|accomplishments?|milestones?|wins?)"],
    "emotion_log"     : [r"how (?:was i|have i been|am i) feeling", r"my (?:mood|emotions?) (?:in|during|last|this)"],
    "goal"            : [r"(?:my|what are my|tell me my) (?:goals?|ambitions?|aspirations?)", r"what (?:goals?|dreams?) (?:have i set|did i have|do i have)"],
    "decision"        : [r"(?:my|what) (?:decisions?|choices?) (?:i made|have i made|this year|last year)"],
    "relationship"    : [r"(?:about|tell me about) (?:my (?:friend|family|mom|dad|sister|brother|partner|colleague))"],
    "habit"           : [r"(?:my|what are my) (?:habits?|routines?|practices?)"],
    "financial"       : [r"(?:my|about my) (?:finances?|money|savings?|spending|budget)"],
    "learning"        : [r"(?:what have i been|my) (?:learning|studying|reading)"],
    "creative_work"   : [r"(?:my|about my) (?:creative work|projects?|writing|art|music|novel|game|app)"],
    "reflection"      : [r"(?:my|what are my) (?:reflections?|insights?|lessons? learned|realizations?)"],
    "conflict"        : [r"(?:my|any) (?:conflicts?|fights?|arguments?|issues?) (?:with|i had)"],
    "social_event"    : [r"(?:my|what) (?:parties|events?|celebrations?|gatherings?) (?:i attended|i went to)"],
    "gratitude"       : [r"(?:what am i|my) (?:grateful for|thankful for|gratitude)"],
}


def detect_recall_type(text: str) -> dict:
    """
    Detect what kind of recall query this is.

    Returns:
        {
          "type"       : "chronological" | "monthly" | "collection"
                         | "timeline" | "general",
          "collection" : str | None,
          "year"       : int | None,
          "month"      : int | None,
          "keyword"    : str | None,
          "target_date": date | None,
        }
    """
    text_lower = text.lower().strip()

    # ── Timeline (day/week/life story) ────────────────────
    for p in TIMELINE_PATTERNS:
        if re.search(p, text_lower):
            # Check if there's a specific ISO date in the query
            iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", text_lower)
            target_date_val = None
            if iso_match:
                try:
                    target_date_val = date.fromisoformat(iso_match.group(1))
                except Exception:
                    pass
            keyword = _extract_keyword(text_lower)
            logger.info(f"[Recall] Type=timeline | kw={keyword} | date={target_date_val}")
            return {"type": "timeline", "collection": None,
                    "year": None, "month": None, "keyword": keyword,
                    "target_date": target_date_val}

    # ── Specific date: "what happened on March 23" or "on 2026-02-15" ──
    # ISO date anywhere in query
    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", text_lower)
    if iso_match:
        try:
            target_date_val = date.fromisoformat(iso_match.group(1))
            logger.info(f"[Recall] Type=timeline | iso_date={target_date_val}")
            return {"type": "timeline", "collection": None,
                    "year": None, "month": None, "keyword": None,
                    "target_date": target_date_val}
        except Exception:
            pass

    # Natural language date: "on March 23", "on 15th January"
    specific_date_match = re.search(
        r"(?:on|for) (?:the )?(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(?:of\s+)?(january|february|march|april|may|june|july|august|"
        r"september|october|november|december)(?:\s+(\d{4}))?",
        text_lower
    )
    if not specific_date_match:
        specific_date_match = re.search(
            r"(?:on|for) (?:the )?(january|february|march|april|may|june|july|"
            r"august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(\d{4}))?",
            text_lower
        )
    if specific_date_match:
        from backend.processing.collection_classifier import extract_event_date
        target = extract_event_date(text)
        if target:
            logger.info(f"[Recall] Type=timeline | specific_date={target}")
            return {"type": "timeline", "collection": None,
                    "year": None, "month": None, "keyword": None,
                    "target_date": target}

    # ── Chronological ─────────────────────────────────────
    for p in CHRONOLOGICAL_PATTERNS:
        if re.search(p, text_lower):
            col = "experience"
            if "memory" in text_lower or "message" in text_lower:
                col = None
            elif "achievement" in text_lower or "win" in text_lower:
                col = "achievement"
            elif "decision" in text_lower:
                col = "decision"
            logger.info(f"[Recall] Type=chronological | collection={col}")
            return {"type": "chronological", "collection": col,
                    "year": None, "month": None, "keyword": None,
                    "target_date": None}

    # ── Monthly ───────────────────────────────────────────
    for p in MONTHLY_PATTERNS:
        m = re.search(p, text_lower)
        if m:
            month_str = m.group(1)
            year_str  = m.group(2) if len(m.groups()) > 1 else None
            month = MONTH_MAP.get(month_str)
            year  = int(year_str) if year_str else date.today().year
            logger.info(f"[Recall] Type=monthly | {year}-{month:02d}")
            return {"type": "monthly", "collection": None,
                    "year": year, "month": month, "keyword": None,
                    "target_date": None}

    # ── Collection-specific ───────────────────────────────
    for collection, patterns in COLLECTION_RECALL_PATTERNS.items():
        for p in patterns:
            if re.search(p, text_lower):
                keyword = _extract_keyword(text_lower)
                logger.info(f"[Recall] Type=collection | collection={collection} | kw={keyword}")
                return {"type": "collection", "collection": collection,
                        "year": None, "month": None, "keyword": keyword,
                        "target_date": None}

    # ── General ───────────────────────────────────────────
    return {"type": "general", "collection": None,
            "year": None, "month": None, "keyword": None,
            "target_date": None}


def _extract_keyword(text: str) -> Optional[str]:
    """Extract the most meaningful keyword from a recall query."""
    stopwords = {
        "what", "when", "where", "tell", "about", "my", "me", "the",
        "have", "been", "that", "this", "with", "from", "they", "were",
        "will", "your", "know", "first", "thing", "experience", "shared",
        "happened", "during", "recall", "remember", "show", "give", "list"
    }
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    keywords = [w for w in words if w not in stopwords]
    return keywords[0] if keywords else None


# ── Main recall function ──────────────────────────────────

def recall(user_id: str, query: str) -> Optional[dict]:
    """
    Main recall entry point. Routes query to the right retrieval path.

    Returns:
        {
          "found"    : bool,
          "answer"   : str,
          "source"   : str,   # "chronological" | "monthly" | "collection" | None
          "entries"  : list,  # raw entries used
        }
    or None if this is not a recall query (caller should use normal RAG)
    """
    recall_type = detect_recall_type(query)

    if recall_type["type"] == "general":
        return None   # not a recall query — use normal RAG

    rtype = recall_type["type"]

    # ── Timeline recall ────────────────────────────────────
    if rtype == "timeline":
        return _recall_timeline(user_id, recall_type.get("target_date"),
                                recall_type.get("keyword"), query)

    # ── Chronological recall ───────────────────────────────
    if rtype == "chronological":
        return _recall_chronological(user_id, recall_type["collection"], query)

    # ── Monthly recall ─────────────────────────────────────
    if rtype == "monthly":
        return _recall_monthly(user_id, recall_type["year"], recall_type["month"])

    # ── Collection recall ──────────────────────────────────
    if rtype == "collection":
        return _recall_collection(
            user_id, recall_type["collection"],
            recall_type["keyword"], query
        )

    return None


def _recall_timeline(user_id: str, target_date: Optional[date],
                     keyword: Optional[str], query: str) -> dict:
    """
    Route timeline recall queries:
    - Specific date → get_day_summary
    - "last week" / "my week" → get_week_summary
    - "life story" / "most significant" → get_most_significant_moments
    - "when did I feel X" → get_timeline_by_mood
    - keyword → search_timeline
    """
    from backend.memory.life_timeline import (
        get_day_summary, get_week_summary, get_most_significant_moments,
        get_timeline_by_mood, get_timeline_by_person, search_timeline,
        get_life_story
    )
    text_lower = query.lower()

    # ── Specific date ──────────────────────────────────────
    if target_date:
        day = get_day_summary(user_id, target_date)
        if day.get("entry_count", 0) == 0:
            return {
                "found" : False,
                "answer": f"I don't have any events recorded for {target_date}.",
                "source": "timeline",
                "entries": [],
            }
        answer = f"**{target_date}:**\n{day['summary']}"
        if day.get("dominant_emotion"):
            answer += f"\n\nMood: {day['dominant_emotion']}"
        if day.get("people") and day["people"] != "[]":
            import json as _j
            people = _j.loads(day["people"]) if isinstance(day["people"], str) else day["people"]
            if people:
                answer += f"\nWith: {', '.join(people[:3])}"
        return {"found": True, "answer": answer, "source": "timeline", "entries": []}

    # ── Life story / most significant ─────────────────────
    if any(p in text_lower for p in ["life story", "most significant", "most important moments"]):
        moments = get_most_significant_moments(user_id, limit=5, min_significance=7)
        if not moments:
            return {"found": False,
                    "answer": "I don't have enough significant moments recorded yet.",
                    "source": "timeline", "entries": []}
        lines = [f"• [{str(m['entry_date'])[:10]}] [{m['collection_type']}] {m['content'][:80]}"
                 for m in moments]
        answer = "Your most significant moments:\n" + "\n".join(lines)
        return {"found": True, "answer": answer, "source": "timeline", "entries": moments}

    # ── Week summary ───────────────────────────────────────
    if any(p in text_lower for p in ["last week", "this week", "my week", "walk me through"]):
        week = get_week_summary(user_id)
        if not week["found"]:
            return {"found": False, "answer": week["summary"],
                    "source": "timeline", "entries": []}
        answer = f"**Your week ({week['period']}):**\n{week['summary']}"
        return {"found": True, "answer": answer, "source": "timeline",
                "entries": week["entries"]}

    # ── Mood-based recall ──────────────────────────────────
    mood_match = re.search(
        r"(?:when did i (?:last )?feel|last time i felt?|moments? (?:when|i felt?))\s+"
        r"(happy|sad|stressed|excited|proud|grateful|angry|tired|motivated|scared|content)",
        text_lower
    )
    if mood_match:
        mood    = mood_match.group(1)
        moments = get_timeline_by_mood(user_id, mood, limit=5)
        if not moments:
            return {"found": False,
                    "answer": f"I don't have any moments recorded when you felt {mood}.",
                    "source": "timeline", "entries": []}
        lines = [f"• [{str(m['entry_date'])[:10]}] {m['content'][:80]}"
                 for m in moments]
        answer = f"Moments when you felt **{mood}**:\n" + "\n".join(lines)
        return {"found": True, "answer": answer, "source": "timeline", "entries": moments}

    # ── Keyword search ─────────────────────────────────────
    if keyword:
        results = search_timeline(user_id, keyword, limit=5)
        if results:
            lines = [f"• [{str(r['entry_date'])[:10]}] {r['content'][:80]}"
                     for r in results]
            answer = f"Timeline entries matching '{keyword}':\n" + "\n".join(lines)
            return {"found": True, "answer": answer, "source": "timeline", "entries": results}

    # ── Recent life story ──────────────────────────────────
    story = get_life_story(user_id, limit_days=7)
    if not story:
        return {"found": False,
                "answer": "I don't have enough timeline data yet. Keep sharing your life with me!",
                "source": "timeline", "entries": []}
    lines = [f"• [{str(d['day_date'])[:10]}] {d['summary'][:80]}" for d in story]
    answer = "Your recent life story:\n" + "\n".join(lines)
    return {"found": True, "answer": answer, "source": "timeline", "entries": story}


def _recall_chronological(user_id: str, collection: Optional[str], query: str) -> dict:
    """Find the oldest entry in a collection and summarize its context chain."""
    from backend.memory.collection_store import (
        get_earliest_in_collection, get_conversation_chain,
        keyword_search_collection
    )
    from backend.memory.memory_manager import get_earliest_memories

    # Try typed collection first
    if collection:
        entry = get_earliest_in_collection(user_id, collection)
    else:
        # Search all collections for oldest
        entry = None
        for col in ["experience", "achievement", "emotion_log", "decision"]:
            e = get_earliest_in_collection(user_id, col)
            if e:
                if entry is None or (e.get("event_date") or e["created_at"]) < (entry.get("event_date") or entry["created_at"]):
                    entry = e

    if not entry:
        # Fall back to raw memories table
        earliest = get_earliest_memories(user_id, limit=3)
        if not earliest:
            return {"found": False, "answer": "I don't have any memories stored yet.", "source": "chronological", "entries": []}
        lines = [f'• [{str(m["created_at"])[:10]}] "{m["message"]}"' for m in earliest]
        answer = "Here are the earliest things you shared with me:\n" + "\n".join(lines) + "\n\nThese are your first memories in SoulSync. 🧠"
        return {"found": True, "answer": answer, "source": "chronological", "entries": earliest}

    # Get conversation chain around that date
    anchor = entry.get("event_date") or entry["created_at"].date() if hasattr(entry["created_at"], "date") else date.fromisoformat(str(entry["created_at"])[:10])
    chain  = get_conversation_chain(user_id, anchor, window_days=3)

    answer = _summarize_chain(chain, entry, query, context="first")
    return {"found": True, "answer": answer, "source": "chronological", "entries": chain}


def _recall_monthly(user_id: str, year: int, month: int) -> dict:
    """Retrieve or build monthly summary."""
    from backend.memory.monthly_summary import build_monthly_summary, get_monthly_summary

    # Check if user has any data for this month first
    from backend.memory.collection_store import get_entries_in_month
    entries = get_entries_in_month(user_id, year, month)

    if not entries:
        # No data — return honest answer without trying to build/store
        month_name = list(MONTH_MAP.keys())[month - 1].capitalize()
        return {
            "found" : False,
            "answer": f"I don't have any memories from {month_name} {year} yet. "
                      f"As you share more with me, I'll be able to recall specific months.",
            "source": "monthly",
            "entries": [],
        }

    summary = build_monthly_summary(user_id, year, month)

    if not summary or not summary.get("full_summary"):
        return {
            "found" : False,
            "answer": f"I don't have enough data for {year}-{month:02d} yet.",
            "source": "monthly",
            "entries": [],
        }

    month_name = list(MONTH_MAP.keys())[month - 1].capitalize()
    answer = f"**{month_name} {year}:**\n\n{summary['full_summary']}"

    # Add structured highlights if available
    experiences  = summary.get("experiences") or []
    achievements = summary.get("achievements") or []
    if isinstance(experiences, str):
        import json as _json
        try: experiences = _json.loads(experiences)
        except: experiences = []
    if isinstance(achievements, str):
        import json as _json
        try: achievements = _json.loads(achievements)
        except: achievements = []

    if experiences:
        answer += f"\n\n**Experiences:** {', '.join(experiences[:3])}"
    if achievements:
        answer += f"\n\n**Achievements:** {', '.join(achievements[:3])}"

    return {"found": True, "answer": answer, "source": "monthly", "entries": []}


def _recall_collection(user_id: str, collection: str,
                       keyword: Optional[str], query: str) -> dict:
    """Search a specific collection and summarize results."""
    from backend.memory.collection_store import (
        query_collection, keyword_search_collection, get_conversation_chain
    )

    # Special case: goal queries → use personal_info goals timeline
    if collection == "goal":
        from backend.memory.personal_info import get_goals_timeline, get_facts_in_period
        # Check if query mentions a time period
        period_match = re.search(
            r"(january|february|march|april|may|june|july|august|september|october|november|december|"
            r"this year|last year|this month|last month|\d{4})",
            query.lower()
        )
        if period_match:
            period_str = period_match.group(1)
            today = date.today()
            if period_str == "this year":
                start = date(today.year, 1, 1)
                end   = today
            elif period_str == "last year":
                start = date(today.year - 1, 1, 1)
                end   = date(today.year - 1, 12, 31)
            elif period_str == "this month":
                start = date(today.year, today.month, 1)
                end   = today
            elif period_str == "last month":
                m = today.month - 1 or 12
                y = today.year if today.month > 1 else today.year - 1
                start = date(y, m, 1)
                end   = today.replace(day=1) - __import__("datetime").timedelta(days=1)
            elif period_str.isdigit():
                year  = int(period_str)
                start = date(year, 1, 1)
                end   = date(year, 12, 31)
            else:
                month = MONTH_MAP.get(period_str)
                if month:
                    start = date(today.year, month, 1)
                    end   = today
                else:
                    start = date(today.year, 1, 1)
                    end   = today

            goals = get_facts_in_period(user_id, start, end, context="goal")
            if goals:
                lines = [f"• [{str(g.get('event_date') or g['created_at'])[:10]}] {g['value']}"
                         for g in goals]
                answer = f"Your goals during that period:\n" + "\n".join(lines) + " 💪"
                return {"found": True, "answer": answer, "source": "collection", "entries": goals}

        # No period — return all goals with timeline
        goals = get_goals_timeline(user_id)
        if goals:
            lines = [f"• [{str(g.get('event_date') or g['created_at'])[:10]}] {g['value']}"
                     for g in goals]
            answer = "Your goals over time:\n" + "\n".join(lines) + " 💪"
            return {"found": True, "answer": answer, "source": "collection", "entries": goals}

    # Try keyword search first, then broad collection query
    if keyword:
        entries = keyword_search_collection(user_id, keyword, collection, limit=5)
    else:
        entries = query_collection(user_id, collection, limit=5, order="DESC")

    if not entries:
        return {
            "found" : False,
            "answer": f"I don't have any {collection.replace('_', ' ')} memories stored yet.",
            "source": "collection",
            "entries": [],
        }

    answer = _summarize_chain(entries, entries[0], query, context=collection)
    return {"found": True, "answer": answer, "source": "collection", "entries": entries}


def _summarize_chain(chain: list, anchor_entry: dict,
                     query: str, context: str = "") -> str:
    """
    Use Groq to summarize a chain of related entries into a natural response.
    Falls back to a structured list if Groq fails.
    """
    if not chain:
        return f"I found this memory: {anchor_entry.get('content', '')}"

    try:
        from backend.core.ai_service import client, GROQ_MODEL

        lines = []
        for e in chain[:10]:
            col      = e.get("collection", "memory")
            date_str = str(e.get("event_date") or e.get("created_at", ""))[:10]
            lines.append(f"[{col}] ({date_str}) {e.get('content', e.get('message', ''))[:150]}")

        data_block = "\n".join(lines)

        if context == "first":
            instruction = "Summarize the user's FIRST/EARLIEST memory in 2-3 warm sentences. Mention the date and what they shared."
        else:
            instruction = f"Summarize these {context.replace('_',' ')} memories in 2-3 warm, personal sentences. Be specific."

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a personal AI companion recalling memories for the user. Be warm and specific."},
                {"role": "user",   "content": f"{instruction}\n\nMemories:\n{data_block}\n\nUser asked: {query}"},
            ],
            max_tokens=250,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.warning(f"[Recall] Groq summarization failed: {e}")
        # Structured fallback
        lines = []
        for entry in chain[:5]:
            date_str = str(entry.get("event_date") or entry.get("created_at", ""))[:10]
            content  = entry.get("content") or entry.get("message", "")
            lines.append(f"• [{date_str}] {content[:100]}")
        return "Here's what I found:\n" + "\n".join(lines)
