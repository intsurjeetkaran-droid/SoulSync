"""
SoulSync AI - Database Configuration
=====================================

Central configuration management for all database connections and services.
This module loads environment variables and provides a Settings singleton
that is used throughout the application.

Active Services:
    - MongoDB (primary database for all data storage)
    - Redis (caching layer for responses and sessions)
    - FAISS (local vector search for semantic memory retrieval)

Disabled Services:
    - MySQL (reserved for future payment/subscription system)

Environment Variables:
    MONGODB_URL: MongoDB connection string (default: mongodb://localhost:27017)
    MONGODB_DB: Database name (default: soulsync_db)
    REDIS_URL: Redis connection URL (default: redis://localhost:6379)
    REDIS_TTL_CHAT: Cache TTL for chat responses in seconds (default: 600)
    REDIS_TTL_SESSION: Cache TTL for user sessions in seconds (default: 86400)
    REDIS_TTL_DEFAULT: Default cache TTL in seconds (default: 300)
    GROQ_API_KEY: API key for Groq LLM service (required)
    JWT_SECRET_KEY: Secret key for JWT token signing
    JWT_ALGORITHM: JWT algorithm (default: HS256)
    JWT_EXPIRE_MINUTES: JWT token expiration in minutes (default: 10080 = 7 days)
    ENABLE_PAYMENTS: Feature flag to enable MySQL/payments (default: False)
    ENABLE_REDIS: Feature flag to enable Redis caching (default: True)

Usage:
    >>> from db.config import settings
    >>> print(settings.MONGODB_URL)
    >>> settings.validate()
"""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger("soulsync.db.config")

# ── Environment Loading ──────────────────────────────────────────────
# Load .env file from project root (three levels up from this file)
_env_path = os.path.join(os.path.dirname(__file__), "../../../.env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path)
    logger.debug(f"[Config] Loaded environment from {_env_path}")
else:
    logger.warning(f"[Config] .env file not found at {_env_path}, using system environment variables")


class Settings:
    """
    Central configuration class for SoulSync AI.
    
    This class manages all configuration settings for the application,
    including database connections, API keys, and feature flags.
    Settings are loaded from environment variables with sensible defaults.
    
    Attributes:
        MONGODB_URL: Connection string for MongoDB Atlas or local instance
        MONGODB_DB: Name of the MongoDB database
        REDIS_URL: Connection URL for Redis cache
        REDIS_TTL_CHAT: Time-to-live for cached chat responses (seconds)
        REDIS_TTL_SESSION: Time-to-live for user session data (seconds)
        REDIS_TTL_DEFAULT: Default TTL for other cached data (seconds)
        GROQ_API_KEY: API key for Groq LLM service
        JWT_SECRET_KEY: Secret key for JWT token signing
        JWT_ALGORITHM: Algorithm used for JWT encoding/decoding
        JWT_EXPIRE_MINUTES: JWT token validity period in minutes
        ENABLE_PAYMENTS: Feature flag for payment system (MySQL)
        ENABLE_REDIS: Feature flag for Redis caching
        MYSQL_*: MySQL connection parameters (disabled by default)
    """
    
    # ── MongoDB (Primary Database) ──────────────────────────────────
    # MongoDB is the primary data store for all user data, messages,
    # memories, tasks, and other application data.
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    """MongoDB connection string. Supports both local and Atlas cloud connections."""
    
    MONGODB_DB: str = os.getenv("MONGODB_DB", "soulsync_db")
    """Name of the MongoDB database to use."""
    
    # ── Redis (Caching Layer) ───────────────────────────────────────
    # Redis provides fast in-memory caching for AI responses, user sessions,
    # and frequently accessed data to reduce database load and API calls.
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    """Redis connection URL. Format: redis://[:password]@host:port/db"""
    
    REDIS_TTL_CHAT: int = int(os.getenv("REDIS_TTL_CHAT", "600"))
    """TTL for cached chat responses (default: 10 minutes)."""
    
    REDIS_TTL_SESSION: int = int(os.getenv("REDIS_TTL_SESSION", "86400"))
    """TTL for user session data (default: 24 hours)."""
    
    REDIS_TTL_DEFAULT: int = int(os.getenv("REDIS_TTL_DEFAULT", "300"))
    """Default TTL for other cached data (default: 5 minutes)."""
    
    # ── Feature Flags ───────────────────────────────────────────────
    # Control which features are enabled in the application.
    
    ENABLE_PAYMENTS: bool = False
    """
    Feature flag for payment system.
    When False (default), MySQL and payment features are disabled.
    Set to True and configure MySQL to enable subscription/wallet features.
    """
    
    ENABLE_REDIS: bool = True
    """
    Feature flag for Redis caching.
    When True, Redis is used for caching responses and sessions.
    When False, the application works without caching (graceful degradation).
    """
    
    # ── MySQL (DISABLED - Future Payments) ──────────────────────────
    # MySQL is reserved for future payment and subscription features.
    # These settings are kept here for easy re-enabling when needed.
    
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    """MySQL server hostname."""
    
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    """MySQL server port."""
    
    MYSQL_DB: str = os.getenv("MYSQL_DB", "soulsync_finance")
    """MySQL database name for financial data."""
    
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    """MySQL username."""
    
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    """MySQL password (should be set via environment variable in production)."""
    
    @property
    def MYSQL_URL(self) -> str:
        """
        Construct MySQL connection URL for async SQLAlchemy.
        
        Returns:
            Complete MySQL connection URL string.
        """
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
            f"?charset=utf8mb4"
        )
    
    # ── Application Settings ────────────────────────────────────────
    # Core application configuration for AI and authentication.
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    """
    Groq API key for LLM inference.
    REQUIRED: Must be set in environment for AI chat functionality.
    Get your key from: https://console.groq.com/keys
    """
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    """
    Secret key for JWT token signing.
    IMPORTANT: Change this in production for security!
    """
    
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    """Algorithm used for JWT token encoding/decoding."""
    
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))
    """
    JWT token expiration time in minutes.
    Default: 10080 minutes = 7 days
    """
    
    def validate(self) -> None:
        """
        Validate configuration settings on application startup.
        
        This method checks that all required settings are properly configured
        and logs warnings for any missing or insecure configurations.
        
        Should be called during application initialization.
        
        Raises:
            No exceptions raised - validation is informational only.
        """
        # Check required API keys
        if not self.GROQ_API_KEY:
            logger.warning(
                "[Config] GROQ_API_KEY is not set. AI chat functionality will not work. "
                "Set the environment variable or add it to .env file."
            )
        else:
            logger.debug("[Config] GROQ_API_KEY is configured")
        
        # Check JWT security
        if self.JWT_SECRET_KEY == "change-me-in-production":
            logger.warning(
                "[Config] JWT_SECRET_KEY is using default value. "
                "Change it in production for security!"
            )
        
        # Log active configuration
        logger.info(
            f"[Config] Configuration loaded | "
            f"MongoDB={self.MONGODB_URL}/{self.MONGODB_DB} | "
            f"Redis={'enabled' if self.ENABLE_REDIS else 'disabled'} ({self.REDIS_URL}) | "
            f"Payments={'enabled' if self.ENABLE_PAYMENTS else 'disabled'} | "
            f"JWT expiry={self.JWT_EXPIRE_MINUTES} minutes"
        )
        
        # Log feature status
        if self.ENABLE_PAYMENTS:
            logger.info(f"[Config] Payment system enabled | MySQL={self.MYSQL_URL}")
        else:
            logger.debug("[Config] Payment system disabled (ENABLE_PAYMENTS=False)")


# ── Global Settings Instance ────────────────────────────────────────
# Singleton instance used throughout the application
settings = Settings()
"""
Global settings singleton.
Import this instance to access configuration throughout the application.

Example:
    from db.config import settings
    mongo_url = settings.MONGODB_URL
"""