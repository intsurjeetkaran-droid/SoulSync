"""
SoulSync AI - Memory API Router
Endpoints:
  POST /save-memory  : save a message to memory
  GET  /get-memory   : fetch memories for a user
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.memory.memory_manager import (
    save_memory,
    ensure_user_exists,
    get_memories,
    get_memory_count,
)

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────

class SaveMemoryRequest(BaseModel):
    user_id: str
    role:    str      # 'user' or 'assistant'
    message: str


class SaveMemoryResponse(BaseModel):
    status:  str
    user_id: str
    role:    str
    message: str


class GetMemoryResponse(BaseModel):
    user_id:      str
    total:        int
    memories:     list


# ─── POST /save-memory ────────────────────────────────────

@router.post("/save-memory", response_model=SaveMemoryResponse)
async def save_memory_endpoint(request: SaveMemoryRequest):
    """
    Save a single message to the user's memory.
    Role must be 'user' or 'assistant'.
    """
    if request.role not in ("user", "assistant"):
        raise HTTPException(
            status_code=400,
            detail="Role must be 'user' or 'assistant'."
        )
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        ensure_user_exists(request.user_id)
        save_memory(request.user_id, request.role, request.message)
        return SaveMemoryResponse(
            status="saved",
            user_id=request.user_id,
            role=request.role,
            message=request.message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory save error: {str(e)}")


# ─── GET /get-memory ──────────────────────────────────────

@router.get("/get-memory/{user_id}", response_model=GetMemoryResponse)
async def get_memory_endpoint(user_id: str, limit: int = 20):
    """
    Fetch recent memories for a user.
    Optional query param: ?limit=20
    """
    try:
        memories = get_memories(user_id, limit=limit)
        total    = get_memory_count(user_id)
        return GetMemoryResponse(
            user_id=user_id,
            total=total,
            memories=memories,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory fetch error: {str(e)}")


# ─── GET /monthly-summary ─────────────────────────────────

@router.get("/monthly-summary/{user_id}/{year}/{month}")
async def get_monthly_summary_endpoint(user_id: str, year: int, month: int):
    """
    Get or build the monthly summary for a specific year-month.
    Example: GET /monthly-summary/rohit_123/2025/6
    """
    try:
        from backend.memory.monthly_summary import build_monthly_summary
        summary = build_monthly_summary(user_id, year, month)
        return {"user_id": user_id, "year": year, "month": month, **summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monthly summary error: {str(e)}")


# ─── GET /collections-summary ─────────────────────────────

@router.get("/collections-summary/{user_id}")
async def get_collections_summary(user_id: str):
    """
    Get count of entries per collection type for a user.
    Shows how many experiences, achievements, emotions, etc. are stored.
    """
    try:
        from backend.memory.collection_store import get_all_collections_summary
        summary = get_all_collections_summary(user_id)
        total   = sum(summary.values())
        return {
            "user_id"     : user_id,
            "total_entries": total,
            "by_collection": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collections summary error: {str(e)}")


# ─── GET /timeline/{user_id}/{date} ───────────────────────

@router.get("/timeline/{user_id}/{date_str}")
async def get_timeline_day(user_id: str, date_str: str):
    """
    Get the life timeline for a specific date.
    date_str format: YYYY-MM-DD
    Example: GET /timeline/rohit_123/2026-03-23
    """
    try:
        from datetime import date as _date
        from backend.memory.life_timeline import get_day_summary, get_timeline_for_date
        target = _date.fromisoformat(date_str)
        entries = get_timeline_for_date(user_id, target)
        summary = get_day_summary(user_id, target)
        return {
            "user_id"  : user_id,
            "date"     : date_str,
            "summary"  : summary,
            "entries"  : entries,
            "count"    : len(entries),
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline error: {str(e)}")


# ─── GET /timeline/{user_id}/range ────────────────────────

@router.get("/timeline-range/{user_id}")
async def get_timeline_range_endpoint(user_id: str,
                                       start: str, end: str,
                                       collection: Optional[str] = None,
                                       min_significance: int = 1):
    """
    Get timeline entries within a date range.
    Example: GET /timeline-range/rohit_123?start=2026-01-01&end=2026-03-31
    """
    try:
        from datetime import date as _date
        from backend.memory.life_timeline import get_timeline_range
        entries = get_timeline_range(
            user_id, _date.fromisoformat(start), _date.fromisoformat(end),
            collection_type=collection, min_significance=min_significance
        )
        return {"user_id": user_id, "start": start, "end": end,
                "count": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /timeline-significant/{user_id} ──────────────────

@router.get("/timeline-significant/{user_id}")
async def get_significant_moments(user_id: str,
                                   limit: int = 10,
                                   min_significance: int = 7):
    """Get the most significant moments in the user's life."""
    try:
        from backend.memory.life_timeline import get_most_significant_moments
        moments = get_most_significant_moments(user_id, limit, min_significance)
        return {"user_id": user_id, "count": len(moments), "moments": moments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /life-story/{user_id} ────────────────────────────

@router.get("/life-story/{user_id}")
async def get_life_story_endpoint(user_id: str, days: int = 30):
    """
    Get the user's life story — day summaries for the last N days.
    """
    try:
        from backend.memory.life_timeline import get_life_story
        story = get_life_story(user_id, limit_days=days)
        return {"user_id": user_id, "days": days,
                "count": len(story), "story": story}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
