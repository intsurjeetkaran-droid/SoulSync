"""
SoulSync AI - Memory API Router
================================

Endpoints for managing user memories, including saving, retrieving, and analyzing
stored memories. This router provides access to the complete memory system including:
- Raw message storage
- Monthly summaries
- Collection statistics
- Life timeline
- Significant moments
- Life story generation

Endpoints:
    POST /save-memory              - Save a single message to memory
    GET  /get-memory/{user_id}     - Fetch recent memories for a user
    GET  /monthly-summary/{user_id}/{year}/{month} - Get monthly summary
    GET  /collections-summary/{user_id} - Get collection type statistics
    GET  /timeline/{user_id}/{date} - Get timeline for a specific date
    GET  /timeline-range/{user_id} - Get timeline entries in date range
    GET  /timeline-significant/{user_id} - Get most significant moments
    GET  /life-story/{user_id}     - Get day summaries for last N days

Usage:
    # Save a memory
    POST /api/v1/save-memory
    {"user_id": "user123", "role": "user", "message": "I felt happy today"}
    
    # Get memories
    GET /api/v1/get-memory/user123?limit=10
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.memory.memory_manager import (
    save_memory,
    ensure_user_exists,
    get_memories,
    get_memory_count,
)

logger = logging.getLogger("soulsync.api.memory")
router = APIRouter()


# ─── Request/Response Schemas ────────────────────────────────────────────

class SaveMemoryRequest(BaseModel):
    """Request schema for saving a memory."""
    user_id: str
    role: str  # 'user' or 'assistant'
    message: str


class SaveMemoryResponse(BaseModel):
    """Response schema for memory save operation."""
    status: str
    user_id: str
    role: str
    message: str


class GetMemoryResponse(BaseModel):
    """Response schema for retrieving memories."""
    user_id: str
    total: int
    memories: list


# ─── POST /save-memory ───────────────────────────────────────────────────

@router.post("/save-memory", response_model=SaveMemoryResponse)
async def save_memory_endpoint(request: SaveMemoryRequest):
    """
    Save a single message to the user's memory.
    
    This endpoint stores a raw message (either from user or assistant) in the
    memory system. Messages are stored with role information for later retrieval.
    
    Args:
        request: SaveMemoryRequest with user_id, role, and message
        
    Returns:
        SaveMemoryResponse confirming the save
        
    Raises:
        HTTPException(400): If role is invalid or message is empty
        HTTPException(500): If save operation fails
    """
    # Validate role
    if request.role not in ("user", "assistant"):
        logger.warning(f"[Memory API] Invalid role: {request.role}")
        raise HTTPException(
            status_code=400,
            detail="Role must be 'user' or 'assistant'."
        )
    
    # Validate message
    if not request.message.strip():
        logger.warning(f"[Memory API] Empty message from user={request.user_id}")
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    try:
        ensure_user_exists(request.user_id)
        save_memory(request.user_id, request.role, request.message)
        logger.info(f"[Memory API] Saved memory: user={request.user_id} | role={request.role}")
        
        return SaveMemoryResponse(
            status="saved",
            user_id=request.user_id,
            role=request.role,
            message=request.message,
        )
    except Exception as e:
        logger.error(f"[Memory API] Save failed: {e}")
        raise HTTPException(status_code=500, detail=f"Memory save error: {str(e)}")


# ─── GET /get-memory ─────────────────────────────────────────────────────

@router.get("/get-memory/{user_id}", response_model=GetMemoryResponse)
async def get_memory_endpoint(user_id: str, limit: int = 20):
    """
    Fetch recent memories for a user.
    
    Args:
        user_id: Unique user identifier
        limit: Maximum number of memories to return (default: 20)
        
    Returns:
        GetMemoryResponse with total count and list of memories
        
    Raises:
        HTTPException(500): If fetch operation fails
    """
    try:
        memories = get_memories(user_id, limit=limit)
        total = get_memory_count(user_id)
        logger.debug(f"[Memory API] Retrieved {len(memories)} memories for user={user_id}")
        
        return GetMemoryResponse(
            user_id=user_id,
            total=total,
            memories=memories,
        )
    except Exception as e:
        logger.error(f"[Memory API] Fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Memory fetch error: {str(e)}")


# ─── GET /monthly-summary ────────────────────────────────────────────────

@router.get("/monthly-summary/{user_id}/{year}/{month}")
async def get_monthly_summary_endpoint(user_id: str, year: int, month: int):
    """
    Get or build the monthly summary for a specific year-month.
    
    Monthly summaries aggregate all memories and activities from a given month
    into a comprehensive overview, including mood trends, activities, and key events.
    
    Args:
        user_id: Unique user identifier
        year: Year (e.g., 2025)
        month: Month number (1-12)
        
    Returns:
        Monthly summary with aggregated data
        
    Raises:
        HTTPException(400): If month is invalid
        HTTPException(500): If summary generation fails
        
    Example:
        GET /api/v1/monthly-summary/rohit_123/2025/6
    """
    if not (1 <= month <= 12):
        logger.warning(f"[Memory API] Invalid month: {month}")
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")
    
    try:
        from backend.memory.monthly_summary import build_monthly_summary
        summary = build_monthly_summary(user_id, year, month)
        logger.info(f"[Memory API] Generated monthly summary: user={user_id} | {year}-{month}")
        
        return {"user_id": user_id, "year": year, "month": month, **summary}
    except Exception as e:
        logger.error(f"[Memory API] Monthly summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Monthly summary error: {str(e)}")


# ─── GET /collections-summary ────────────────────────────────────────────

@router.get("/collections-summary/{user_id}")
async def get_collections_summary(user_id: str):
    """
    Get count of entries per collection type for a user.
    
    Shows how many experiences, achievements, emotions, etc. are stored
    in the collection store. Useful for understanding the distribution
    of memory types.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Dictionary with collection names as keys and counts as values
        
    Raises:
        HTTPException(500): If summary generation fails
    """
    try:
        from backend.memory.collection_store import get_all_collections_summary
        summary = get_all_collections_summary(user_id)
        total = sum(summary.values())
        logger.debug(f"[Memory API] Collections summary: user={user_id} | total={total}")
        
        return {
            "user_id": user_id,
            "total_entries": total,
            "by_collection": summary,
        }
    except Exception as e:
        logger.error(f"[Memory API] Collections summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Collections summary error: {str(e)}")


# ─── GET /timeline/{user_id}/{date} ──────────────────────────────────────

@router.get("/timeline/{user_id}/{date_str}")
async def get_timeline_day(user_id: str, date_str: str):
    """
    Get the life timeline for a specific date.
    
    Returns all timeline entries for the specified date, including
    memories, activities, and significant events.
    
    Args:
        user_id: Unique user identifier
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Timeline entries for the specified date with summary
        
    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If timeline retrieval fails
        
    Example:
        GET /api/v1/timeline/rohit_123/2026-03-23
    """
    try:
        from datetime import date as _date
        from backend.memory.life_timeline import get_day_summary, get_timeline_for_date
        
        target = _date.fromisoformat(date_str)
        entries = get_timeline_for_date(user_id, target)
        summary = get_day_summary(user_id, target)
        logger.debug(f"[Memory API] Timeline for date: user={user_id} | date={date_str} | entries={len(entries)}")
        
        return {
            "user_id": user_id,
            "date": date_str,
            "summary": summary,
            "entries": entries,
            "count": len(entries),
        }
    except ValueError:
        logger.warning(f"[Memory API] Invalid date format: {date_str}")
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    except Exception as e:
        logger.error(f"[Memory API] Timeline retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Timeline error: {str(e)}")


# ─── GET /timeline-range ─────────────────────────────────────────────────

@router.get("/timeline-range/{user_id}")
async def get_timeline_range_endpoint(
    user_id: str,
    start: str,
    end: str,
    collection: Optional[str] = None,
    min_significance: int = 1
):
    """
    Get timeline entries within a date range.
    
    Allows filtering by collection type and minimum significance level
    to focus on the most important events.
    
    Args:
        user_id: Unique user identifier
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        collection: Optional collection type filter (e.g., "achievement", "experience")
        min_significance: Minimum significance score (1-10, default: 1)
        
    Returns:
        Timeline entries within the date range
        
    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If retrieval fails
        
    Example:
        GET /api/v1/timeline-range/rohit_123?start=2026-01-01&end=2026-03-31
    """
    try:
        from datetime import date as _date
        from backend.memory.life_timeline import get_timeline_range
        
        entries = get_timeline_range(
            user_id,
            _date.fromisoformat(start),
            _date.fromisoformat(end),
            collection_type=collection,
            min_significance=min_significance
        )
        logger.debug(f"[Memory API] Timeline range: user={user_id} | {start} to {end} | entries={len(entries)}")
        
        return {
            "user_id": user_id,
            "start": start,
            "end": end,
            "count": len(entries),
            "entries": entries
        }
    except Exception as e:
        logger.error(f"[Memory API] Timeline range failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /timeline-significant ───────────────────────────────────────────

@router.get("/timeline-significant/{user_id}")
async def get_significant_moments(
    user_id: str,
    limit: int = 10,
    min_significance: int = 7
):
    """
    Get the most significant moments in the user's life.
    
    Returns timeline entries sorted by significance score, useful for
    highlighting major life events and milestones.
    
    Args:
        user_id: Unique user identifier
        limit: Maximum number of moments to return (default: 10)
        min_significance: Minimum significance score (1-10, default: 7)
        
    Returns:
        List of significant moments sorted by importance
        
    Raises:
        HTTPException(500): If retrieval fails
    """
    try:
        from backend.memory.life_timeline import get_most_significant_moments
        moments = get_most_significant_moments(user_id, limit, min_significance)
        logger.debug(f"[Memory API] Significant moments: user={user_id} | count={len(moments)}")
        
        return {"user_id": user_id, "count": len(moments), "moments": moments}
    except Exception as e:
        logger.error(f"[Memory API] Significant moments failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /life-story ─────────────────────────────────────────────────────

@router.get("/life-story/{user_id}")
async def get_life_story_endpoint(user_id: str, days: int = 30):
    """
    Get the user's life story — day summaries for the last N days.
    
    This creates a narrative view of the user's recent life by combining
    daily summaries into a cohesive story format.
    
    Args:
        user_id: Unique user identifier
        days: Number of days to include (default: 30)
        
    Returns:
        List of day summaries for the specified period
        
    Raises:
        HTTPException(500): If story generation fails
    """
    try:
        from backend.memory.life_timeline import get_life_story
        story = get_life_story(user_id, limit_days=days)
        logger.debug(f"[Memory API] Life story: user={user_id} | days={days} | entries={len(story)}")
        
        return {
            "user_id": user_id,
            "days": days,
            "count": len(story),
            "story": story
        }
    except Exception as e:
        logger.error(f"[Memory API] Life story failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))