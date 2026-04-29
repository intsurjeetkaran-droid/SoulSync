"""
SoulSync AI - Suggestion API Router
Endpoints:
  GET /suggestions/{user_id}  : get smart suggestions for user
  GET /analysis/{user_id}     : get full pattern analysis
"""

from fastapi import APIRouter, HTTPException
from backend.suggestion.suggestion_engine import get_suggestion_summary
from backend.suggestion.analyzer          import get_full_analysis

router = APIRouter()


# ─── GET /suggestions ─────────────────────────────────────

@router.get("/suggestions/{user_id}")
async def get_suggestions(user_id: str):
    """
    Analyze user patterns and return smart suggestions.
    """
    try:
        result = get_suggestion_summary(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /analysis ────────────────────────────────────────

@router.get("/analysis/{user_id}")
async def get_analysis(user_id: str):
    """
    Return full pattern analysis for a user.
    """
    try:
        result = get_full_analysis(user_id)
        return {"user_id": user_id, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
