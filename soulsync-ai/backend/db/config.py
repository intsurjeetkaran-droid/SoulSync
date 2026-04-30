"""
SoulSync AI - Database Configuration
Active: MongoDB (primary and only database)
Active: Redis (caching)
Active: FAISS (vector search)
Disabled: MySQL (reserved for future payments/subscriptions)
"""

import os
import logging
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), "../../../.env")
load_dotenv(dotenv_path=_env_path)

logger = logging.getLogger("soulsync.db.config")


class Settings:
    # ── MongoDB (primary DB) ──────────────────────────────
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB: str  = os.getenv("MONGODB_DB", "soulsync_db")

    # ── Redis (caching) ───────────────────────────────────
    REDIS_URL: str       = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_TTL_CHAT: int  = int(os.getenv("REDIS_TTL_CHAT", "600"))
    REDIS_TTL_SESSION: int = int(os.getenv("REDIS_TTL_SESSION", "86400"))
    REDIS_TTL_DEFAULT: int = int(os.getenv("REDIS_TTL_DEFAULT", "300"))

    # ── Feature flags ─────────────────────────────────────
    ENABLE_PAYMENTS: bool = False   # MySQL/payments disabled until needed
    ENABLE_REDIS: bool    = True

    # ── MySQL (DISABLED — future payments) ────────────────
    # Kept here so re-enabling is a one-line change
    MYSQL_HOST: str     = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int     = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DB: str       = os.getenv("MYSQL_DB", "soulsync_finance")
    MYSQL_USER: str     = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")

    @property
    def MYSQL_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
            f"?charset=utf8mb4"
        )

    # ── App ───────────────────────────────────────────────
    GROQ_API_KEY: str       = os.getenv("GROQ_API_KEY", "")
    JWT_SECRET_KEY: str     = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str      = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

    def validate(self) -> None:
        if not self.GROQ_API_KEY:
            logger.warning("[Config] GROQ_API_KEY is not set")
        logger.info(
            f"[Config] MongoDB={self.MONGODB_URL}/{self.MONGODB_DB} | "
            f"Redis={self.REDIS_URL} | Payments={'enabled' if self.ENABLE_PAYMENTS else 'disabled'}"
        )


settings = Settings()
