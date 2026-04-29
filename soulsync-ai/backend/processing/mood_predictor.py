"""
SoulSync AI - Mood Prediction Engine
Feature: Mood Prediction Engine (Phase 1)

Uses past mood logs + activity data + time patterns
to predict the user's current emotional state.

Prediction logic:
  1. Load user's mood history into Pandas DataFrame
  2. Analyze patterns by day-of-week and hour-of-day
  3. Compare current time to historical patterns
  4. Generate prediction + confidence score
  5. Trigger proactive support if low mood predicted

Mood scale: 1-10
  1-3  : Very Low  (needs support)
  4-5  : Low       (gentle check-in)
  6-7  : Neutral   (normal interaction)
  8-9  : Good      (positive reinforcement)
  10   : Excellent (celebrate)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from backend.memory.database import get_connection, get_cursor


# ─── Mood Score Mapping ───────────────────────────────────
MOOD_TO_SCORE = {
    "excellent"  : 10,
    "very happy" : 9,
    "happy"      : 8,
    "good"       : 7,
    "neutral"    : 6,
    "okay"       : 5,
    "low"        : 4,
    "sad"        : 3,
    "stressed"   : 3,
    "anxious"    : 3,
    "tired"      : 3,
    "angry"      : 2,
    "depressed"  : 1,
    "terrible"   : 1,
}

SCORE_TO_LABEL = {
    range(1, 4) : "very low",
    range(4, 6) : "low",
    range(6, 8) : "neutral",
    range(8, 10): "good",
}


def score_to_label(score: float) -> str:
    """Convert numeric score to mood label."""
    if score >= 9:   return "excellent"
    if score >= 7.5: return "good"
    if score >= 5.5: return "neutral"
    if score >= 3.5: return "low"
    return "very low"


# ─── Log Mood ─────────────────────────────────────────────

def log_mood(user_id: str, mood: str, mood_score: int = None,
             note: str = None, source: str = "manual"):
    """
    Log a mood entry for a user.

    Args:
        user_id    : unique user identifier
        mood       : mood label (happy, stressed, tired, etc.)
        mood_score : 1-10 score (auto-derived from mood if None)
        note       : optional note
        source     : 'manual' or 'auto' (extracted from chat)
    """
    if mood_score is None:
        mood_score = MOOD_TO_SCORE.get(mood.lower(), 5)

    now         = datetime.now()
    day_of_week = now.strftime("%A")   # Monday, Tuesday, etc.
    hour_of_day = now.hour

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO mood_logs
                (user_id, mood, mood_score, note, day_of_week, hour_of_day, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (user_id, mood.lower(), mood_score, note,
             day_of_week, hour_of_day, source)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def auto_log_mood_from_emotion(user_id: str, emotion: str, note: str = None):
    """
    Auto-log mood from extracted emotion (called by memory processing).
    Maps activity extractor emotions to mood scores.
    """
    emotion_to_mood = {
        "happy"    : ("happy",   8),
        "motivated": ("good",    8),
        "neutral"  : ("neutral", 6),
        "tired"    : ("tired",   3),
        "stressed" : ("stressed",3),
        "sad"      : ("sad",     2),
        "angry"    : ("angry",   2),
    }
    mood, score = emotion_to_mood.get(emotion.lower(), ("neutral", 5))
    log_mood(user_id, mood, score, note=note, source="auto")


# ─── Load Mood History ────────────────────────────────────

def load_mood_dataframe(user_id: str, days: int = 30) -> pd.DataFrame:
    """
    Load mood history into a Pandas DataFrame.

    Returns DataFrame with columns:
      mood, mood_score, day_of_week, hour_of_day, created_at
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT mood, mood_score, day_of_week, hour_of_day, created_at
            FROM mood_logs
            WHERE user_id = %s
              AND created_at >= NOW() - INTERVAL '%s days'
            ORDER BY created_at ASC;
            """,
            (user_id, days)
        )
        rows = cur.fetchall()
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(r) for r in rows])
        df["created_at"] = pd.to_datetime(df["created_at"])
        return df
    finally:
        cur.close()
        conn.close()


# ─── Analyze Patterns ─────────────────────────────────────

def analyze_mood_patterns(df: pd.DataFrame) -> dict:
    """
    Analyze mood patterns from historical data.

    Returns:
        dict with:
          by_day      : avg mood score per day of week
          by_hour     : avg mood score per hour block
          trend       : improving / declining / stable
          worst_day   : day with lowest avg mood
          best_day    : day with highest avg mood
          avg_score   : overall average
    """
    if df.empty:
        return {}

    # Average by day of week
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    by_day = (
        df.groupby("day_of_week")["mood_score"]
        .mean()
        .reindex(day_order)
        .dropna()
        .round(2)
        .to_dict()
    )

    # Average by hour block (morning/afternoon/evening/night)
    df["hour_block"] = pd.cut(
        df["hour_of_day"],
        bins=[0, 6, 12, 17, 21, 24],
        labels=["night", "morning", "afternoon", "evening", "late night"],
        right=False
    )
    by_hour = (
        df.groupby("hour_block", observed=True)["mood_score"]
        .mean()
        .round(2)
        .to_dict()
    )

    # Trend: compare first half vs second half
    mid = len(df) // 2
    if mid > 0:
        first_half  = df.iloc[:mid]["mood_score"].mean()
        second_half = df.iloc[mid:]["mood_score"].mean()
        diff = second_half - first_half
        if diff > 0.5:
            trend = "improving"
        elif diff < -0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    avg_score = round(df["mood_score"].mean(), 2)
    worst_day = min(by_day, key=by_day.get) if by_day else None
    best_day  = max(by_day, key=by_day.get) if by_day else None

    return {
        "by_day"   : by_day,
        "by_hour"  : {str(k): v for k, v in by_hour.items()},
        "trend"    : trend,
        "worst_day": worst_day,
        "best_day" : best_day,
        "avg_score": avg_score,
    }


# ─── Predict Current Mood ─────────────────────────────────

def predict_mood(user_id: str) -> dict:
    """
    Predict the user's current mood based on historical patterns.

    Returns:
        dict with:
          predicted_mood  : mood label
          predicted_score : 1-10 float
          confidence      : low / medium / high
          reason          : explanation
          needs_support   : bool (True if predicted score <= 4)
          proactive_msg   : message to show proactively
          patterns        : full pattern analysis
    """
    df = load_mood_dataframe(user_id, days=30)

    if df.empty or len(df) < 3:
        return {
            "predicted_mood" : "unknown",
            "predicted_score": 5.0,
            "confidence"     : "low",
            "reason"         : "Not enough mood history yet. Keep logging!",
            "needs_support"  : False,
            "proactive_msg"  : None,
            "patterns"       : {},
            "data_points"    : 0,
        }

    patterns = analyze_mood_patterns(df)

    # Get current time context
    now         = datetime.now()
    current_day = now.strftime("%A")
    current_hour = now.hour

    # Determine hour block
    if current_hour < 6:
        hour_block = "night"
    elif current_hour < 12:
        hour_block = "morning"
    elif current_hour < 17:
        hour_block = "afternoon"
    elif current_hour < 21:
        hour_block = "evening"
    else:
        hour_block = "late night"

    # Build prediction from patterns
    scores     = []
    reasons    = []
    confidence = "low"

    # Day-based prediction
    if current_day in patterns.get("by_day", {}):
        day_score = patterns["by_day"][current_day]
        scores.append(day_score)
        reasons.append(f"historically {score_to_label(day_score)} on {current_day}s")
        confidence = "medium"

    # Hour-based prediction
    if hour_block in patterns.get("by_hour", {}):
        hour_score = patterns["by_hour"][hour_block]
        scores.append(hour_score)
        reasons.append(f"typically {score_to_label(hour_score)} in the {hour_block}")

    # Recent trend
    if patterns.get("trend") == "declining":
        scores.append(max(1, patterns["avg_score"] - 1))
        reasons.append("mood has been declining recently")
    elif patterns.get("trend") == "improving":
        scores.append(min(10, patterns["avg_score"] + 0.5))
        reasons.append("mood has been improving recently")

    # Calculate final prediction
    if scores:
        predicted_score = round(float(np.mean(scores)), 1)
        if len(scores) >= 2:
            confidence = "high"
    else:
        predicted_score = patterns.get("avg_score", 5.0)
        reasons.append("based on overall average mood")

    predicted_mood = score_to_label(predicted_score)
    needs_support  = predicted_score <= 4.0

    # Generate proactive message
    proactive_msg = None
    if needs_support:
        if current_day == patterns.get("worst_day"):
            proactive_msg = (
                f"Hey, {current_day}s tend to be tough for you. "
                f"I'm here if you need to talk. How are you feeling today?"
            )
        else:
            proactive_msg = (
                f"I noticed you've been feeling {predicted_mood} lately. "
                f"Want to talk about what's on your mind?"
            )
    elif predicted_score >= 8:
        proactive_msg = (
            f"You tend to feel great at this time! "
            f"Great moment to tackle something important. 🚀"
        )

    return {
        "predicted_mood" : predicted_mood,
        "predicted_score": predicted_score,
        "confidence"     : confidence,
        "reason"         : " | ".join(reasons) if reasons else "based on history",
        "needs_support"  : needs_support,
        "proactive_msg"  : proactive_msg,
        "patterns"       : patterns,
        "data_points"    : len(df),
    }
