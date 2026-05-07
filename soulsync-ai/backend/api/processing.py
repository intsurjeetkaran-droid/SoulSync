"""
SoulSync AI - Processing API Router
Endpoints:
  POST /process-memory   : extract structured data from text
  GET  /get-activities   : fetch structured activities for a user
  GET  /emotion-summary  : get emotion counts for a user
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.processing.extractor     import extract_memory
from backend.processing.activity_store import save_activity, get_activities, get_emotion_summary
from backend.memory.memory_manager    import ensure_user_exists

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────

class ProcessRequest(BaseModel):
    user_id : str
    text    : str
    use_ai  : bool = False   # set True for AI-enhanced extraction


class ProcessResponse(BaseModel):
    user_id     : str
    raw_text    : str
    activity_id : str
    extracted   : dict


# ─── POST /process-memory ─────────────────────────────────

@router.post("/process-memory", response_model=ProcessResponse)
async def process_memory(request: ProcessRequest):
    """
    Extract structured data from user text and save to DB.

    Example input:
      "I felt tired and skipped gym today"

    Example output:
      { "emotion": "tired", "activity": "gym",
        "status": "missed", "productivity": "low",
        "summary": "User felt tired and missed gym" }
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        ensure_user_exists(request.user_id)

        # Extract structured data
        extracted = extract_memory(request.text, use_ai=request.use_ai)

        # Save to activities table
        activity_id = save_activity(request.user_id, request.text, extracted)

        return ProcessResponse(
            user_id=request.user_id,
            raw_text=request.text,
            activity_id=activity_id,
            extracted=extracted,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# ─── GET /get-activities ──────────────────────────────────

@router.get("/get-activities/{user_id}")
async def get_activities_endpoint(user_id: str, limit: int = 20):
    """Fetch recent structured activities for a user."""
    try:
        activities = get_activities(user_id, limit=limit)
        return {"user_id": user_id, "count": len(activities), "activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /emotion-summary ─────────────────────────────────

@router.get("/emotion-summary/{user_id}")
async def emotion_summary(user_id: str):
    """Get emotion frequency counts for a user."""
    try:
        summary = get_emotion_summary(user_id)
        return {"user_id": user_id, "emotions": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
