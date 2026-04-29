"""
SoulSync AI - Memory Extractor
Converts raw user text into structured JSON data.

Uses two approaches:
  1. Rule-based  : fast keyword matching (always runs)
  2. AI-based    : uses the loaded model for richer extraction

Output format:
{
  "emotion"     : "tired",
  "activity"    : "gym",
  "status"      : "missed",
  "productivity": "low",
  "summary"     : "User felt tired and skipped gym"
}
"""

import re
import json

# ─── Keyword Dictionaries ─────────────────────────────────

EMOTION_KEYWORDS = {
    "happy"      : ["happy", "great", "amazing", "excited", "joyful", "good", "fantastic", "wonderful"],
    "sad"        : ["sad", "unhappy", "depressed", "down", "miserable", "upset", "heartbroken"],
    "tired"      : ["tired", "exhausted", "sleepy", "drained", "fatigue", "worn out", "burnout"],
    "stressed"   : ["stressed", "anxious", "overwhelmed", "nervous", "worried", "tense", "pressure"],
    "angry"      : ["angry", "frustrated", "annoyed", "irritated", "mad", "furious"],
    "motivated"  : ["motivated", "inspired", "energetic", "pumped", "focused", "productive"],
    "neutral"    : ["okay", "fine", "alright", "normal", "average"],
}

ACTIVITY_KEYWORDS = {
    "gym"        : ["gym", "workout", "exercise", "training", "weights", "cardio", "run", "running"],
    "work"       : ["work", "office", "meeting", "project", "task", "deadline", "coding", "programming"],
    "study"      : ["study", "studying", "reading", "learning", "course", "exam", "homework"],
    "sleep"      : ["sleep", "slept", "nap", "rest", "bed", "insomnia"],
    "eating"     : ["eat", "ate", "food", "lunch", "dinner", "breakfast", "meal", "diet"],
    "meditation" : ["meditate", "meditation", "mindfulness", "yoga", "breathing"],
    "social"     : ["friends", "family", "party", "hangout", "meet", "call", "chat"],
    "hobby"      : ["music", "guitar", "drawing", "painting", "gaming", "reading", "cooking"],
}

STATUS_KEYWORDS = {
    "completed"  : ["completed", "finished", "done", "achieved", "accomplished", "succeeded"],
    "missed"     : ["missed", "skipped", "didn't", "couldn't", "failed", "avoided", "forgot"],
    "started"    : ["started", "began", "initiated", "tried"],
    "planned"    : ["planning", "plan", "will", "going to", "want to", "intend"],
    "ongoing"    : ["doing", "working on", "in progress", "currently"],
}

PRODUCTIVITY_MAP = {
    "high"  : ["productive", "focused", "accomplished", "efficient", "great day", "lot done"],
    "low"   : ["unproductive", "distracted", "couldn't focus", "wasted", "lazy", "procrastinated"],
    "medium": ["okay", "average", "some", "a bit", "partially"],
}


# ─── Rule-Based Extractor ─────────────────────────────────

def extract_with_rules(text: str) -> dict:
    """
    Fast keyword-based extraction.
    Returns partial results — AI layer fills in the rest.
    """
    text_lower = text.lower()
    result = {
        "emotion"     : None,
        "activity"    : None,
        "status"      : None,
        "productivity": None,
        "summary"     : None,
    }

    # Detect emotion
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            result["emotion"] = emotion
            break

    # Detect activity
    for activity, keywords in ACTIVITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            result["activity"] = activity
            break

    # Detect status
    for status, keywords in STATUS_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            result["status"] = status
            break

    # Detect productivity
    for level, keywords in PRODUCTIVITY_MAP.items():
        if any(kw in text_lower for kw in keywords):
            result["productivity"] = level
            break

    # Default fallbacks
    if not result["emotion"]:
        result["emotion"] = "neutral"
    if not result["status"]:
        result["status"] = "mentioned"
    if not result["productivity"]:
        result["productivity"] = "medium"

    # Auto-generate summary
    parts = []
    if result["emotion"] != "neutral":
        parts.append(f"felt {result['emotion']}")
    if result["activity"]:
        parts.append(f"{result['status']} {result['activity']}")
    result["summary"] = "User " + " and ".join(parts) if parts else f"User said: {text[:80]}"

    return result


# ─── AI-Based Extractor ───────────────────────────────────

def extract_with_ai(text: str) -> dict:
    """
    Uses Groq API to extract structured memory data from user text.
    Falls back to rule-based if AI output is not parseable.
    """
    try:
        from backend.core.ai_service import extract_with_groq
        return extract_with_groq(text)
    except Exception:
        pass  # Fall back to rule-based

    return None


# ─── Main Extract Function ────────────────────────────────

def extract_memory(text: str, use_ai: bool = False) -> dict:
    """
    Main extraction function.
    Always runs rule-based extraction.
    Optionally enhances with AI (slower but richer).

    Args:
        text   : raw user input text
        use_ai : whether to also run AI extraction

    Returns:
        dict with emotion, activity, status, productivity, summary
    """
    # Always run rule-based (fast, reliable)
    rule_result = extract_with_rules(text)

    if use_ai:
        ai_result = extract_with_ai(text)
        if ai_result:
            # Merge: AI fills in what rules missed
            for key in rule_result:
                if not rule_result[key] and ai_result.get(key):
                    rule_result[key] = ai_result[key]
            # AI summary is usually better
            if ai_result.get("summary"):
                rule_result["summary"] = ai_result["summary"]

    return rule_result
