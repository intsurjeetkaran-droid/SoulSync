"""
SoulSync AI - Main FastAPI Application
Entry point for the backend server
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat         import router as chat_router
from backend.api.memory       import router as memory_router
from backend.api.processing   import router as processing_router
from backend.api.suggestion   import router as suggestion_router
from backend.api.tasks        import router as tasks_router
from backend.api.voice        import router as voice_router
from backend.api.optimization import router as optimization_router
from backend.api.unique_features import router as unique_router
from backend.auth.routes      import router as auth_router

logger = logging.getLogger("soulsync.main")


# ─── Startup / Shutdown ───────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB migrations on startup."""
    try:
        from backend.memory.schema import create_tables
        from backend.auth.models   import migrate_auth_schema
        create_tables()
        migrate_auth_schema()
        logger.info("[Main] DB ready")
    except Exception as e:
        logger.error(f"[Main] DB startup error: {e}")
    yield


# ─── App Setup ────────────────────────────────────────────
app = FastAPI(
    title       = "SoulSync AI",
    description = "A personal AI companion with memory and personalization",
    version     = "2.0.0",
    lifespan    = lifespan,
)

# ─── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ─── Routers ──────────────────────────────────────────────
app.include_router(auth_router,         prefix="/api/v1", tags=["Auth"])
app.include_router(chat_router,         prefix="/api/v1", tags=["Chat"])
app.include_router(memory_router,       prefix="/api/v1", tags=["Memory"])
app.include_router(processing_router,   prefix="/api/v1", tags=["Processing"])
app.include_router(suggestion_router,   prefix="/api/v1", tags=["Suggestions"])
app.include_router(tasks_router,        prefix="/api/v1", tags=["Tasks"])
app.include_router(voice_router,        prefix="/api/v1", tags=["Voice"])
app.include_router(optimization_router, prefix="/api/v1", tags=["Optimization"])
app.include_router(unique_router,       prefix="/api/v1", tags=["Unique Features"])


# ─── Root ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "project": "SoulSync AI",
        "version": "2.0.0",
        "status" : "running",
        "docs"   : "/docs",
    }
