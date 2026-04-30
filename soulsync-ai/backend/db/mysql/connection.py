"""
SoulSync AI - MySQL Connection (SQLAlchemy async + aiomysql)
Provides async engine, session factory, and table initialization.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from ..config import settings
from .models import Base

logger = logging.getLogger("soulsync.db.mysql")

# Module-level engine (singleton)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


def get_mysql_engine() -> AsyncEngine:
    """Return (or create) the singleton async MySQL engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.MYSQL_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
        )
        logger.info(f"[MySQL] Engine created → {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")
    return _engine


def _get_session_factory() -> async_sessionmaker:
    """Return (or create) the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_mysql_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a MySQL session.
    Commits on success, rolls back on exception.

    Usage:
        async with get_mysql_session() as session:
            result = await session.execute(...)
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_mysql_tables() -> None:
    """
    Create all MySQL tables on startup.
    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS semantics.
    """
    engine = get_mysql_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[MySQL] All tables initialized ✅")
    except Exception as e:
        logger.error(f"[MySQL] Table initialization failed: {e}", exc_info=True)
        raise


async def close_mysql_connection() -> None:
    """Dispose the engine on app shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("[MySQL] Connection pool disposed")
