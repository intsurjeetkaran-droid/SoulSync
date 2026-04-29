"""
SoulSync AI - Pattern Analyzer
Uses Pandas to analyze user activity data and detect patterns.

Analyzes:
  - Emotion frequency
  - Activity completion vs missed rate
  - Productivity trends
  - Positive streaks
"""

import pandas as pd
from backend.processing.activity_store import get_activities


def load_user_dataframe(user_id: str, limit: int = 50) -> pd.DataFrame:
    """
    Load user activities from DB into a Pandas DataFrame.

    Returns DataFrame with columns:
      id, user_id, raw_text, emotion, activity,
      status, productivity, summary, created_at
    """
    activities = get_activities(user_id, limit=limit)

    if not activities:
        return pd.DataFrame()

    df = pd.DataFrame(activities)

    # Convert created_at to datetime
    df["created_at"] = pd.to_datetime(df["created_at"])

    # Fill nulls with 'unknown'
    df.fillna("unknown", inplace=True)

    return df


def analyze_emotions(df: pd.DataFrame) -> dict:
    """
    Count emotion frequencies.
    Returns: {"tired": 5, "stressed": 3, "happy": 2, ...}
    """
    if df.empty or "emotion" not in df.columns:
        return {}

    counts = df["emotion"].value_counts().to_dict()
    return counts


def analyze_activities(df: pd.DataFrame) -> dict:
    """
    Analyze activity completion vs missed rates.
    Returns: {"gym": {"completed": 2, "missed": 4}, ...}
    """
    if df.empty:
        return {}

    result = {}
    grouped = df.groupby(["activity", "status"]).size().reset_index(name="count")

    for _, row in grouped.iterrows():
        act = row["activity"]
        sts = row["status"]
        cnt = row["count"]
        if act not in result:
            result[act] = {}
        result[act][sts] = cnt

    return result


def analyze_productivity(df: pd.DataFrame) -> dict:
    """
    Analyze productivity distribution.
    Returns: {"high": 3, "medium": 5, "low": 4}
    """
    if df.empty or "productivity" not in df.columns:
        return {}

    return df["productivity"].value_counts().to_dict()


def get_dominant_emotion(df: pd.DataFrame) -> str:
    """Return the most frequent emotion."""
    emotions = analyze_emotions(df)
    if not emotions:
        return "neutral"
    return max(emotions, key=emotions.get)


def get_full_analysis(user_id: str) -> dict:
    """
    Run complete analysis for a user.
    Returns all pattern data in one dict.
    """
    df = load_user_dataframe(user_id)

    if df.empty:
        return {
            "total_entries"   : 0,
            "emotions"        : {},
            "activities"      : {},
            "productivity"    : {},
            "dominant_emotion": "neutral",
            "has_data"        : False,
        }

    return {
        "total_entries"   : len(df),
        "emotions"        : analyze_emotions(df),
        "activities"      : analyze_activities(df),
        "productivity"    : analyze_productivity(df),
        "dominant_emotion": get_dominant_emotion(df),
        "has_data"        : True,
    }
