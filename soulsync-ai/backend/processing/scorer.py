"""
SoulSync AI - Memory Importance Scorer
Feature: Memory Importance Scoring (Phase 1)

Scores each memory on a 0-15 scale based on:
  - Emotional weight  : +5 for strong emotions
  - Repetition        : +3 if activity mentioned before
  - Goal-related      : +4 if related to goals/plans
  - Message length    : +1 for detailed messages
  - Recency boost     : +2 for very recent (handled at retrieval)

Score ranges:
  0-3  : Low importance  → archive after 30 days
  4-7  : Medium          → keep normally
  8-11 : High            → prioritize in RAG
  12+  : Critical        → always keep, never archive
"""

import re

# ─── Emotion Weights ──────────────────────────────────────
HIGH_EMOTION_WORDS = [
    "depressed", "suicidal", "crisis", "breakdown", "devastated",
    "heartbroken", "terrified", "furious", "desperate", "hopeless",
]

STRONG_EMOTION_WORDS = [
    "stressed", "anxious", "overwhelmed", "sad", "angry", "frustrated",
    "excited", "thrilled", "proud", "grateful", "happy", "motivated",
    "tired", "exhausted", "lonely", "scared", "worried",
]

MILD_EMOTION_WORDS = [
    "okay", "fine", "alright", "neutral", "bored", "meh",
]

# ─── Goal Keywords ────────────────────────────────────────
GOAL_KEYWORDS = [
    "goal", "plan", "target", "aim", "objective", "dream", "ambition",
    "want to", "going to", "will", "commit", "promise", "decide",
    "career", "job", "promotion", "study", "learn", "improve",
    "health", "fitness", "relationship", "family", "money", "save",
]

# ─── Repetition Tracking (in-memory, per session) ─────────
_activity_counts: dict = {}


def _reset_session_counts():
    """Reset repetition tracking (call at start of new session)."""
    global _activity_counts
    _activity_counts = {}


# ─── Scoring Function ─────────────────────────────────────

def score_memory(text: str, user_id: str = None,
                 role: str = "user") -> dict:
    """
    Score a memory message for importance.

    Args:
        text    : the message text
        user_id : user identifier (for repetition tracking)
        role    : 'user' or 'assistant' (assistant messages score lower)

    Returns:
        dict with:
          score       : int (0-15)
          level       : 'low' | 'medium' | 'high' | 'critical'
          reasons     : list of scoring reasons
          should_keep : bool
    """
    if not text or not text.strip():
        return {"score": 0, "level": "low", "reasons": [], "should_keep": False}

    text_lower = text.lower()
    score      = 0
    reasons    = []

    # ── Assistant messages score lower ────────────────────
    if role == "assistant":
        return {
            "score"      : 3,
            "level"      : "low",
            "reasons"    : ["assistant message — standard score"],
            "should_keep": True,
        }

    # ── Factor 1: Emotional Weight ─────────────────────────
    if any(w in text_lower for w in HIGH_EMOTION_WORDS):
        score += 7
        reasons.append("critical emotion detected (+7)")
    elif any(w in text_lower for w in STRONG_EMOTION_WORDS):
        score += 4
        reasons.append("strong emotion detected (+4)")
    elif any(w in text_lower for w in MILD_EMOTION_WORDS):
        score += 1
        reasons.append("mild emotion detected (+1)")

    # ── Factor 2: Goal-Related ─────────────────────────────
    goal_hits = sum(1 for kw in GOAL_KEYWORDS if kw in text_lower)
    if goal_hits >= 3:
        score += 4
        reasons.append(f"highly goal-related ({goal_hits} keywords) (+4)")
    elif goal_hits >= 1:
        score += 2
        reasons.append(f"goal-related ({goal_hits} keyword) (+2)")

    # ── Factor 3: Message Length (detail) ─────────────────
    word_count = len(text.split())
    if word_count >= 30:
        score += 2
        reasons.append(f"detailed message ({word_count} words) (+2)")
    elif word_count >= 15:
        score += 1
        reasons.append(f"moderate length ({word_count} words) (+1)")

    # ── Factor 4: Repetition ──────────────────────────────
    # Extract key nouns/activities (simple approach)
    key_words = re.findall(r'\b[a-z]{4,}\b', text_lower)
    key_words = [w for w in key_words
                 if w not in {"that", "this", "with", "have", "been",
                               "from", "they", "were", "will", "just",
                               "about", "when", "what", "your", "very"}]

    if user_id:
        for word in key_words[:5]:  # check top 5 words
            key = f"{user_id}:{word}"
            _activity_counts[key] = _activity_counts.get(key, 0) + 1
            if _activity_counts[key] >= 3:
                score += 3
                reasons.append(f"repeated topic '{word}' ({_activity_counts[key]}x) (+3)")
                break
            elif _activity_counts[key] == 2:
                score += 1
                reasons.append(f"recurring topic '{word}' (+1)")
                break

    # ── Factor 5: Contains specific events ────────────────
    event_patterns = [
        r'\b(today|yesterday|this week|last week|this month)\b',
        r'\b(decided|realized|discovered|achieved|failed|succeeded)\b',
        r'\b(first time|never|always|every day|habit)\b',
    ]
    for pattern in event_patterns:
        if re.search(pattern, text_lower):
            score += 1
            reasons.append(f"specific event/time reference (+1)")
            break

    # ── Determine level ───────────────────────────────────
    if score >= 12:
        level = "critical"
    elif score >= 8:
        level = "high"
    elif score >= 4:
        level = "medium"
    else:
        level = "low"

    should_keep = score >= 3  # archive anything below 3

    return {
        "score"      : min(score, 15),  # cap at 15
        "level"      : level,
        "reasons"    : reasons,
        "should_keep": should_keep,
    }


def get_importance_label(score: int) -> str:
    """Return human-readable label for a score."""
    if score >= 12: return "🔴 Critical"
    if score >= 8:  return "🟠 High"
    if score >= 4:  return "🟡 Medium"
    return "⚪ Low"
