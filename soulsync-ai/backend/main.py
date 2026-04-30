"""
SoulSync AI - Main FastAPI Application
Active databases: MongoDB (primary) + Redis (cache) + FAISS (vectors)
Disabled: MySQL (reserved for future payments)
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat            import router as chat_router
from backend.api.memory          import router as memory_router
from backend.api.processing      import router as processing_router
from backend.api.suggestion      import router as suggestion_router
from backend.api.tasks           import router as tasks_router
from backend.api.voice           import router as voice_router
from backend.api.optimization    import router as optimization_router
from backend.api.unique_features import router as unique_router
from backend.api.payment         import router as payment_router
from backend.auth.routes         import router as auth_router

logger = logging.getLogger("soulsync.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init MongoDB indexes. Shutdown: close connections."""
    # ── MongoDB ───────────────────────────────────────────
    try:
        from backend.db.mongo.connection import init_mongo_indexes, get_mongo_client
        await init_mongo_indexes()
        logger.info("[Main] MongoDB indexes ready ✅")
    except Exception as e:
        logger.error(f"[Main] MongoDB init error: {e}")

    # ── Redis (optional — fail gracefully) ────────────────
    try:
        from backend.db.redis.cache import RedisCacheManager
        cache = RedisCacheManager()
        ok = await cache.ping()
        logger.info(f"[Main] Redis {'connected ✅' if ok else 'unavailable (cache disabled)'}")
    except Exception as e:
        logger.warning(f"[Main] Redis not available: {e}")

    yield

    # ── Shutdown ──────────────────────────────────────────
    try:
        from backend.db.mongo.connection import close_mongo_connection
        await close_mongo_connection()
    except Exception:
        pass
    try:
        from backend.db.redis.cache import close_redis_connection
        await close_redis_connection()
    except Exception:
        pass
    logger.info("[Main] Shutdown complete")


app = FastAPI(
    title       = "SoulSync AI",
    description = "Personal AI companion — MongoDB + Redis + FAISS",
    version     = "3.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://soulsync-vl8w.onrender.com",
        "*",
    ],
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
app.include_router(payment_router,      prefix="/api/v1", tags=["Payments (disabled)"])


@app.get("/")
async def root():
    return {
        "project"  : "SoulSync AI",
        "version"  : "3.0.0",
        "status"   : "running",
        "databases": {"primary": "MongoDB", "cache": "Redis", "vectors": "FAISS"},
        "payments" : "disabled (coming soon)",
        "docs"     : "/docs",
    }
