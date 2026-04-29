"""
SoulSync AI - Optimization API Router
Endpoints:
  GET  /optimize/cache-stats   : view response cache stats
  POST /optimize/cache-clear   : clear the response cache
  GET  /optimize/pool-stats    : view DB connection pool stats
  GET  /optimize/model-info    : AI service info (Groq)
"""

import os
from fastapi import APIRouter, HTTPException

from backend.utils.cache   import response_cache
from backend.utils.db_pool import pool_stats

router = APIRouter()


# ─── GET /optimize/cache-stats ────────────────────────────

@router.get("/optimize/cache-stats")
async def cache_stats():
    """View response cache statistics."""
    return {
        "cache": response_cache.stats(),
        "description": "LRU cache for AI responses (TTL: 10 min)"
    }


# ─── POST /optimize/cache-clear ───────────────────────────

@router.post("/optimize/cache-clear")
async def cache_clear():
    """Clear all cached responses."""
    response_cache.clear()
    return {"status": "cleared", "message": "Response cache cleared."}


# ─── GET /optimize/pool-stats ─────────────────────────────

@router.get("/optimize/pool-stats")
async def db_pool_stats():
    """View database connection pool statistics."""
    try:
        stats = pool_stats()
        return {"pool": stats}
    except Exception as e:
        return {"pool": {"error": str(e), "note": "Pool not initialized yet"}}


# ─── GET /optimize/model-info ─────────────────────────────

@router.get("/optimize/model-info")
async def model_info():
    """Return current AI service and configuration information."""
    groq_key_set = bool(os.getenv("GROQ_API_KEY"))

    return {
        "ai_backend"   : "Groq API",
        "model"        : "llama-3.3-70b-versatile",
        "local_model"  : None,
        "groq_key_set" : groq_key_set,
        "optimizations": [
            "✅ Response LRU cache (200 entries, 10min TTL)",
            "✅ DB connection pool (2-10 connections)",
            "✅ FAISS vector index (per-user, disk-persisted)",
            "✅ Sentence embeddings via sentence-transformers",
            "✅ Groq API (fast cloud inference, no local GPU needed)",
        ]
    }
