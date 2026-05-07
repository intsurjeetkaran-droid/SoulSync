"""
SoulSync AI - Mood Predictor (MongoDB)
Comprehensive mood tracking, detection, and pattern analysis.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("soulsync.mood_predictor")

# ── Mood → Score (1=very negative, 10=very positive) ─────

MOOD_SCORES = {
    # Very positive
    "ecstatic": 10, "elated": 10, "euphoric": 10, "overjoyed": 10,
    "excited": 9, "motivated": 9, "inspired": 9, "energetic": 9, "thrilled": 9,
    "happy": 8, "joyful": 8, "proud": 8, "confident": 8, "grateful": 8,
    "optimistic": 8, "enthusiastic": 8, "amazing": 8, "fantastic": 8,
    # Positive calm
    "content": 7, "peaceful": 7, "calm": 7, "relaxed": 7, "serene": 7,
    "focused": 7, "satisfied": 7, "hopeful": 7, "refreshed": 7, "recharged": 7,
    # Neutral
    "neutral": 5, "okay": 5, "fine": 5, "alright": 5, "normal": 5, "meh": 4,
    "indifferent": 4, "mixed": 4,
    # Mild negative
    "bored": 4, "restless": 4, "distracted": 4, "confused": 4,
    "uncertain": 4, "lonely": 4, "nostalgic": 4, "melancholy": 4,
    # Moderate negative
    "tired": 3, "exhausted": 3, "drained": 3, "stressed": 3, "burnout": 3,
    "anxious": 3, "nervous": 3, "worried": 3, "overwhelmed": 3,
    "frustrated": 3, "irritated": 3, "disappointed": 3, "sad": 3,
    "empty": 3, "numb": 3, "hurt": 3, "lost": 3,
    # Severe negative
    "angry": 2, "furious": 2, "devastated": 2, "heartbroken": 2,
    "depressed": 2, "hopeless": 2, "miserable": 2, "scared": 2,
    "terrified": 2, "panicked": 2, "broken": 2,
    # Crisis
    "suicidal": 1, "destroyed": 1,
}

# ── Emotion → canonical mood ──────────────────────────────

EMOTION_TO_MOOD = {
    "happy": "happy", "joyful": "joyful", "excited": "excited",
    "motivated": "motivated", "proud": "proud", "grateful": "grateful",
    "content": "content", "peaceful": "peaceful", "hopeful": "hopeful",
    "neutral": "neutral", "okay": "okay", "fine": "fine",
    "tired": "tired", "stressed": "stressed", "anxious": "anxious",
    "sad": "sad", "angry": "angry", "frustrated": "frustrated",
    "overwhelmed": "overwhelmed", "lonely": "lonely", "bored": "bored",
    "confused": "confused", "hurt": "hurt", "disappointed": "disappointed",
    "relieved": "content", "focused": "focused", "energetic": "energetic",
    "melancholy": "melancholy", "numb": "numb", "empty": "empty",
    "lost": "lost", "scared": "scared", "nervous": "nervous",
    "worried": "worried", "depressed": "depressed", "heartbroken": "heartbroken",
    "exhausted": "exhausted", "drained": "drained", "burnout": "burnout",
    "irritated": "frustrated", "furious": "angry", "ecstatic": "ecstatic",
    "thrilled": "excited", "inspired": "motivated", "serene": "peaceful",
}

# ── Mood keyword detection ────────────────────────────────

MOOD_KEYWORDS = {
    "ecstatic"    : ["ecstatic", "over the moon", "on top of the world", "best day ever"],
    "excited"     : ["excited", "thrilled", "pumped", "stoked", "hyped", "can't wait"],
    "motivated"   : ["motivated", "inspired", "driven", "energized", "pumped up", "ready to go"],
    "happy"       : ["happy", "great", "amazing", "wonderful", "fantastic", "joyful", "elated", "good mood"],
    "proud"       : ["proud", "accomplished", "achieved", "nailed it", "crushed it", "so proud"],
    "grateful"    : ["grateful", "thankful", "blessed", "appreciate", "lucky", "fortunate"],
    "content"     : ["content", "satisfied", "peaceful", "calm", "relaxed", "serene", "at peace"],
    "hopeful"     : ["hopeful", "optimistic", "looking forward", "things will get better"],
    "focused"     : ["focused", "productive", "in the zone", "on track", "sharp", "clear headed"],
    "neutral"     : ["okay", "fine", "alright", "normal", "neutral", "meh", "so so"],
    "bored"       : ["bored", "boring", "nothing to do", "restless", "uninterested"],
    "lonely"      : ["lonely", "alone", "isolated", "disconnected", "no one to talk to"],
    "confused"    : ["confused", "lost", "unsure", "uncertain", "don't know what to do"],
    "tired"       : ["tired", "exhausted", "drained", "sleepy", "fatigued", "worn out", "no energy"],
    "stressed"    : ["stressed", "stress", "pressure", "overwhelmed", "too much on my plate"],
    "anxious"     : ["anxious", "anxiety", "nervous", "worried", "on edge", "uneasy", "panic"],
    "sad"         : ["sad", "unhappy", "down", "blue", "gloomy", "miserable", "crying", "tears"],
    "angry"       : ["angry", "furious", "mad", "rage", "pissed", "irritated", "annoyed", "livid"],
    "frustrated"  : ["frustrated", "frustrating", "fed up", "had enough", "can't take it"],
    "disappointed": ["disappointed", "let down", "expected more", "didn't go as planned"],
    "scared"      : ["scared", "afraid", "terrified", "fear", "frightened", "dread"],
    "depressed"   : ["depressed", "depression", "hopeless", "empty", "numb", "hollow", "dark place"],
    "heartbroken" : ["heartbroken", "devastated", "broken", "shattered", "crushed"],
    "overwhelmed" : ["overwhelmed", "too much", "can't cope", "drowning", "buried", "feeling overwhelmed"],
    "burnout"     : ["burnout", "burnt out", "burned out", "exhausted from work", "no motivation"],
}


def _run(coro):
    """Run async coroutine safely from both sync and async contexts."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=30)
    except RuntimeError:
        return asyncio.run(coro)


def _db():
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


# ── Detect mood from text ─────────────────────────────────

def detect_mood_from_text(text: str) -> str:
    """Detect mood from raw text using keyword matching."""
    text_lower = text.lower()
    for mood, keywords in MOOD_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return mood
    return "neutral"


# ── Log mood ──────────────────────────────────────────────

def log_mood(user_id: str, mood: str, mood_score: int = None,
             note: str = None, source: str = "manual"):
    if mood_score is None:
        mood_score = MOOD_SCORES.get(mood.lower(), 5)
    now = datetime.utcnow()

    async def _run_inner():
        db = _db()
        await db.mood_logs.insert_one({
            "log_id"     : str(uuid.uuid4()),
            "user_id"    : user_id,
            "mood"       : mood.lower(),
            "mood_score" : mood_score,
            "note"       : note or "",
            "day_of_week": now.strftime("%A"),
            "hour_of_day": now.hour,
            "source"     : source,
            "created_at" : now,
        })
    try:
        _run(_run_inner())
    except Exception as e:
        logger.warning(f"[MoodPredictor] log_mood failed: {e}")


def auto_log_mood_from_emotion(user_id: str, emotion: str, note: str = None):
    """Log mood from a detected emotion string."""
    emotion_lower = emotion.lower().strip()
    mood  = EMOTION_TO_MOOD.get(emotion_lower, emotion_lower)
    score = MOOD_SCORES.get(mood, MOOD_SCORES.get(emotion_lower, 5))
    log_mood(user_id, mood, mood_score=score, note=note, source="auto")


def auto_log_mood_from_text(user_id: str, text: str):
    """Detect and log mood directly from raw conversation text."""
    mood = detect_mood_from_text(text)
    if mood != "neutral":
        score = MOOD_SCORES.get(mood, 5)
        log_mood(user_id, mood, mood_score=score, note=text[:100], source="auto")


# ── Load dataframe ────────────────────────────────────────

def load_mood_dataframe(user_id: str, days: int = 30) -> pd.DataFrame:
    async def _run_inner():
        db = _db()
        since = datetime.utcnow() - timedelta(days=days)
        cursor = db.mood_logs.find(
            {"user_id": user_id, "created_at": {"$gte": since}}
        ).sort("created_at", 1)
        rows = []
        async for doc in cursor:
            rows.append({
                "mood"       : doc.get("mood", "neutral"),
                "mood_score" : doc.get("mood_score", 5),
                "day_of_week": doc.get("day_of_week", ""),
                "hour_of_day": doc.get("hour_of_day", 0),
                "created_at" : doc.get("created_at"),
            })
        return pd.DataFrame(rows)
    try:
        return _run(_run_inner())
    except Exception:
        return pd.DataFrame()


# ── Predict mood ──────────────────────────────────────────

def predict_mood(user_id: str) -> dict:
    df = load_mood_dataframe(user_id, days=14)
    if df.empty:
        return {
            "prediction"    : "neutral",
            "confidence"    : 0.5,
            "avg_score"     : 5.0,
            "recent_score"  : 5.0,
            "trend"         : "stable",
            "message"       : "Not enough data yet. Keep chatting to unlock mood insights!",
            "weekly_pattern": {},
            "best_day"      : None,
            "worst_day"     : None,
            "data_points"   : 0,
        }

    avg    = float(df["mood_score"].mean())
    recent = float(df.tail(5)["mood_score"].mean()) if len(df) >= 5 else avg

    if recent > avg + 0.5:   trend = "improving"
    elif recent < avg - 0.5: trend = "declining"
    else:                     trend = "stable"

    dominant = df["mood"].mode()[0] if not df["mood"].empty else "neutral"

    # Weekly pattern
    weekly = {}
    if "day_of_week" in df.columns and not df["day_of_week"].empty:
        weekly = df.groupby("day_of_week")["mood_score"].mean().round(1).to_dict()

    best_day  = max(weekly, key=weekly.get) if weekly else None
    worst_day = min(weekly, key=weekly.get) if weekly else None
    confidence = min(0.95, 0.5 + len(df) * 0.015)

    if trend == "improving":
        msg = f"Your mood has been improving lately! You tend to feel {dominant} most often."
    elif trend == "declining":
        msg = f"I've noticed your mood has been lower recently. You tend to feel {dominant}. I'm here for you."
    else:
        msg = f"Your mood has been fairly stable. You tend to feel {dominant} most often."

    if best_day:
        msg += f" You seem happiest on {best_day}s."

    return {
        "prediction"    : dominant,
        "avg_score"     : round(avg, 1),
        "recent_score"  : round(recent, 1),
        "trend"         : trend,
        "confidence"    : round(confidence, 2),
        "message"       : msg,
        "weekly_pattern": weekly,
        "best_day"      : best_day,
        "worst_day"     : worst_day,
        "data_points"   : len(df),
    }


# ── Analyze patterns ──────────────────────────────────────

def analyze_mood_patterns(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "by_day": {}, "by_hour": {}, "trend": "unknown",
            "emotion_distribution": {}, "avg_score": 5.0,
            "best_hour": None, "worst_hour": None, "total_logs": 0,
        }

    by_day  = df.groupby("day_of_week")["mood_score"].mean().round(1).to_dict() if "day_of_week" in df.columns else {}
    by_hour = df.groupby("hour_of_day")["mood_score"].mean().round(1).to_dict() if "hour_of_day" in df.columns else {}
    scores  = df["mood_score"].tolist()

    mid = len(scores) // 2
    if mid > 0:
        first_half  = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        if second_half > first_half + 0.5:   trend = "improving"
        elif second_half < first_half - 0.5: trend = "declining"
        else:                                 trend = "stable"
    else:
        trend = "stable"

    emotion_dist = df["mood"].value_counts().to_dict() if "mood" in df.columns else {}
    best_hour    = max(by_hour, key=by_hour.get) if by_hour else None
    worst_hour   = min(by_hour, key=by_hour.get) if by_hour else None

    return {
        "by_day"              : by_day,
        "by_hour"             : by_hour,
        "trend"               : trend,
        "avg_score"           : round(float(df["mood_score"].mean()), 1),
        "emotion_distribution": emotion_dist,
        "best_hour"           : best_hour,
        "worst_hour"          : worst_hour,
        "total_logs"          : len(df),
    }
