"""
SoulSync AI - Mood Predictor (MongoDB)
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("soulsync.mood_predictor")

MOOD_SCORES = {
    "happy": 8, "motivated": 9, "excited": 8, "focused": 7,
    "neutral": 5, "okay": 5,
    "tired": 3, "stressed": 3, "anxious": 3, "sad": 2, "angry": 2,
}


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _db():
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


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
    score = MOOD_SCORES.get(emotion.lower(), 5)
    log_mood(user_id, emotion, mood_score=score, note=note, source="auto")


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
                "mood"       : doc.get("mood"),
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


def predict_mood(user_id: str) -> dict:
    df = load_mood_dataframe(user_id, days=14)
    if df.empty:
        return {"prediction": "neutral", "confidence": 0.5,
                "message": "Not enough data yet. Keep chatting!"}
    avg = df["mood_score"].mean()
    recent = df.tail(3)["mood_score"].mean() if len(df) >= 3 else avg
    trend = "improving" if recent > avg else "declining" if recent < avg else "stable"
    dominant = df["mood"].mode()[0] if not df["mood"].empty else "neutral"
    return {
        "prediction" : dominant,
        "avg_score"  : round(float(avg), 1),
        "trend"      : trend,
        "confidence" : 0.75,
        "message"    : f"Based on your recent patterns, you tend to feel {dominant}.",
    }


def analyze_mood_patterns(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"by_day": {}, "by_hour": {}, "trend": "unknown"}
    by_day  = df.groupby("day_of_week")["mood_score"].mean().round(1).to_dict()
    by_hour = df.groupby("hour_of_day")["mood_score"].mean().round(1).to_dict()
    scores  = df["mood_score"].tolist()
    trend   = "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
    return {"by_day": by_day, "by_hour": by_hour, "trend": trend}
