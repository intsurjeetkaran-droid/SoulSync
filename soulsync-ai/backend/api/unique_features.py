"""
SoulSync AI - Unique Features API Router
Memory scoring, mood tracking — backed by MongoDB.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.processing.scorer import score_memory, get_importance_label

router = APIRouter()


def _get_db():
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


# ─── POST /features/score-memory ──────────────────────────

class ScoreRequest(BaseModel):
    user_id : str
    message : str
    role    : str = "user"


@router.post("/features/score-memory")
async def score_memory_endpoint(request: ScoreRequest):
    try:
        result = score_memory(request.message, request.user_id, request.role)
        return {
            "user_id"    : request.user_id,
            "message"    : request.message[:100],
            "score"      : result["score"],
            "level"      : result["level"],
            "label"      : get_importance_label(result["score"]),
            "reasons"    : result["reasons"],
            "should_keep": result["should_keep"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /features/important-memories ─────────────────────

@router.get("/features/important-memories/{user_id}")
async def get_important_memories(user_id: str, min_score: int = 8, limit: int = 20):
    try:
        db = _get_db()
        cursor = (
            db.messages
            .find({
                "user_id": user_id,
                "role": "user",
                "importance_score": {"$gte": min_score}
            })
            .sort("importance_score", -1)
            .limit(limit)
        )
        memories = []
        async for doc in cursor:
            memories.append({
                "message_id"      : doc.get("message_id"),
                "user_id"         : doc.get("user_id"),
                "role"            : doc.get("role"),
                "message"         : doc.get("content", ""),
                "importance_score": doc.get("importance_score", 5),
                "created_at"      : str(doc.get("created_at", "")),
                "label"           : get_importance_label(doc.get("importance_score", 5)),
            })
        return {"user_id": user_id, "min_score": min_score, "count": len(memories), "memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /features/memory-stats ───────────────────────────

@router.get("/features/memory-stats/{user_id}")
async def memory_stats(user_id: str):
    try:
        db = _get_db()
        pipeline = [
            {"$match": {"user_id": user_id, "role": "user"}},
            {"$group": {
                "_id": None,
                "total"   : {"$sum": 1},
                "critical": {"$sum": {"$cond": [{"$gte": ["$importance_score", 12]}, 1, 0]}},
                "high"    : {"$sum": {"$cond": [{"$and": [{"$gte": ["$importance_score", 8]}, {"$lt": ["$importance_score", 12]}]}, 1, 0]}},
                "medium"  : {"$sum": {"$cond": [{"$and": [{"$gte": ["$importance_score", 4]}, {"$lt": ["$importance_score", 8]}]}, 1, 0]}},
                "low"     : {"$sum": {"$cond": [{"$lt": ["$importance_score", 4]}, 1, 0]}},
                "avg"     : {"$avg": "$importance_score"},
            }}
        ]
        result = await db.messages.aggregate(pipeline).to_list(1)
        stats = result[0] if result else {}
        return {
            "user_id"     : user_id,
            "distribution": {
                "🔴 critical": stats.get("critical", 0),
                "🟠 high"    : stats.get("high", 0),
                "🟡 medium"  : stats.get("medium", 0),
                "⚪ low"     : stats.get("low", 0),
            },
            "total"    : stats.get("total", 0),
            "avg_score": round(stats.get("avg", 0) or 0, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Mood endpoints ───────────────────────────────────────

from backend.processing.mood_predictor import (
    log_mood, predict_mood, load_mood_dataframe,
    analyze_mood_patterns, auto_log_mood_from_emotion
)
from datetime import datetime, timedelta


class LogMoodRequest(BaseModel):
    user_id    : str
    mood       : str
    mood_score : Optional[int] = None
    note       : Optional[str] = None


@router.post("/features/log-mood")
async def log_mood_endpoint(request: LogMoodRequest):
    try:
        log_mood(user_id=request.user_id, mood=request.mood,
                 mood_score=request.mood_score, note=request.note, source="manual")
        return {"status": "logged", "user_id": request.user_id, "mood": request.mood}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/predict-mood/{user_id}")
async def predict_mood_endpoint(user_id: str):
    try:
        result = predict_mood(user_id)
        return {"user_id": user_id, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/mood-history/{user_id}")
async def mood_history(user_id: str, days: int = 7):
    try:
        db = _get_db()
        since = datetime.utcnow() - timedelta(days=days)
        cursor = (
            db.mood_logs
            .find({"user_id": user_id, "created_at": {"$gte": since}})
            .sort("created_at", -1)
        )
        logs = []
        async for doc in cursor:
            logs.append({
                "mood"       : doc.get("mood"),
                "mood_score" : doc.get("mood_score"),
                "day_of_week": doc.get("day_of_week"),
                "hour_of_day": doc.get("hour_of_day"),
                "note"       : doc.get("note"),
                "source"     : doc.get("source"),
                "created_at" : str(doc.get("created_at", "")),
            })
        scores   = [l["mood_score"] for l in logs if l["mood_score"]]
        avg      = round(sum(scores) / len(scores), 1) if scores else None
        trend_up = (scores[0] >= scores[-1]) if len(scores) > 1 else None
        return {
            "user_id"  : user_id, "days": days, "count": len(logs),
            "avg_score": avg,
            "trending" : "up" if trend_up else "down" if trend_up is False else "stable",
            "logs"     : logs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/mood-patterns/{user_id}")
async def mood_patterns(user_id: str):
    try:
        df = load_mood_dataframe(user_id, days=30)
        patterns = analyze_mood_patterns(df)
        return {"user_id": user_id, "data_points": len(df), "patterns": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
