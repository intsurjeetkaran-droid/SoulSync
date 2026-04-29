"""
SoulSync AI - Unique Features API Router
All advanced feature endpoints in one router.

Phase 1:
  POST /features/score-memory      : score a memory for importance
  GET  /features/important-memories: get high-importance memories
  GET  /features/memory-stats      : memory importance distribution
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.processing.scorer import score_memory, get_importance_label
from backend.memory.database   import get_connection, get_cursor

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────

class ScoreRequest(BaseModel):
    user_id : str
    message : str
    role    : str = "user"


# ─── POST /features/score-memory ──────────────────────────

@router.post("/features/score-memory")
async def score_memory_endpoint(request: ScoreRequest):
    """
    Score a memory message for importance.
    Returns score, level, and reasons.
    """
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
async def get_important_memories(user_id: str,
                                  min_score: int = 8,
                                  limit: int = 20):
    """
    Fetch high-importance memories for a user.
    Default: score >= 8 (high + critical only)
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT id, user_id, role, message,
                   COALESCE(importance_score, 5) as importance_score,
                   created_at
            FROM memories
            WHERE user_id = %s
              AND COALESCE(importance_score, 5) >= %s
              AND role = 'user'
            ORDER BY importance_score DESC, created_at DESC
            LIMIT %s;
            """,
            (user_id, min_score, limit)
        )
        rows = cur.fetchall()
        memories = [dict(r) for r in rows]

        # Add label to each
        for m in memories:
            m["label"] = get_importance_label(m["importance_score"])

        return {
            "user_id"  : user_id,
            "min_score": min_score,
            "count"    : len(memories),
            "memories" : memories,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ─── GET /features/memory-stats ───────────────────────────

@router.get("/features/memory-stats/{user_id}")
async def memory_stats(user_id: str):
    """
    Get memory importance distribution for a user.
    Shows how many memories are low/medium/high/critical.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE COALESCE(importance_score,5) >= 12) as critical,
                COUNT(*) FILTER (WHERE COALESCE(importance_score,5) BETWEEN 8 AND 11) as high,
                COUNT(*) FILTER (WHERE COALESCE(importance_score,5) BETWEEN 4 AND 7)  as medium,
                COUNT(*) FILTER (WHERE COALESCE(importance_score,5) < 4)              as low,
                COUNT(*) as total,
                ROUND(AVG(COALESCE(importance_score,5)), 2) as avg_score
            FROM memories
            WHERE user_id = %s AND role = 'user';
            """,
            (user_id,)
        )
        row = cur.fetchone()
        stats = dict(row) if row else {}

        return {
            "user_id"     : user_id,
            "distribution": {
                "🔴 critical": stats.get("critical", 0),
                "🟠 high"    : stats.get("high",     0),
                "🟡 medium"  : stats.get("medium",   0),
                "⚪ low"     : stats.get("low",      0),
            },
            "total"    : stats.get("total",     0),
            "avg_score": stats.get("avg_score", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ═══════════════════════════════════════════════════════════
# FEATURE 2: MOOD PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════

from backend.processing.mood_predictor import (
    log_mood, predict_mood, load_mood_dataframe,
    analyze_mood_patterns, auto_log_mood_from_emotion
)


class LogMoodRequest(BaseModel):
    user_id    : str
    mood       : str
    mood_score : Optional[int] = None
    note       : Optional[str] = None


# ─── POST /features/log-mood ──────────────────────────────

@router.post("/features/log-mood")
async def log_mood_endpoint(request: LogMoodRequest):
    """
    Log a mood entry for a user.
    mood_score is auto-derived from mood label if not provided.
    """
    try:
        log_mood(
            user_id    = request.user_id,
            mood       = request.mood,
            mood_score = request.mood_score,
            note       = request.note,
            source     = "manual"
        )
        return {
            "status" : "logged",
            "user_id": request.user_id,
            "mood"   : request.mood,
            "note"   : request.note,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /features/predict-mood ───────────────────────────

@router.get("/features/predict-mood/{user_id}")
async def predict_mood_endpoint(user_id: str):
    """
    Predict the user's current mood based on historical patterns.
    Returns prediction, confidence, and proactive support message.
    """
    try:
        result = predict_mood(user_id)
        return {"user_id": user_id, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /features/mood-history ───────────────────────────

@router.get("/features/mood-history/{user_id}")
async def mood_history(user_id: str, days: int = 7):
    """
    Get mood history for a user over the last N days.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT mood, mood_score, day_of_week, hour_of_day,
                   note, source, created_at
            FROM mood_logs
            WHERE user_id = %s
              AND created_at >= NOW() - INTERVAL '%s days'
            ORDER BY created_at DESC;
            """,
            (user_id, days)
        )
        rows = cur.fetchall()
        logs = [dict(r) for r in rows]

        # Summary stats
        if logs:
            scores   = [l["mood_score"] for l in logs]
            avg      = round(sum(scores) / len(scores), 1)
            trend_up = scores[0] >= scores[-1] if len(scores) > 1 else None
        else:
            avg      = None
            trend_up = None

        return {
            "user_id"  : user_id,
            "days"     : days,
            "count"    : len(logs),
            "avg_score": avg,
            "trending" : "up" if trend_up else "down" if trend_up is False else "stable",
            "logs"     : logs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ─── GET /features/mood-patterns ──────────────────────────

@router.get("/features/mood-patterns/{user_id}")
async def mood_patterns(user_id: str):
    """
    Get full mood pattern analysis (by day, by hour, trend).
    """
    try:
        df       = load_mood_dataframe(user_id, days=30)
        patterns = analyze_mood_patterns(df)
        return {
            "user_id"    : user_id,
            "data_points": len(df),
            "patterns"   : patterns,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
