"""
SoulSync AI - Auth Security
Password hashing (bcrypt) and JWT token generation/verification.
"""

import os
import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

logger = logging.getLogger("soulsync.auth")

# ─── Config ───────────────────────────────────────────────
SECRET_KEY      = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM       = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES  = int(os.getenv("JWT_EXPIRE_MINUTES", 10080))  # 7 days

# ─── Password hashing ─────────────────────────────────────
# rounds=10 is the default; lower = faster (12 is more secure for prod)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)


def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return pwd_context.verify(plain, hashed)


async def verify_password_async(plain: str, hashed: str) -> bool:
    """
    Run bcrypt verify in a thread pool so it doesn't block the async event loop.
    bcrypt is CPU-intensive — calling it directly in an async route causes timeouts.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, verify_password, plain, hashed)


async def hash_password_async(plain: str) -> str:
    """Run bcrypt hash in a thread pool."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, hash_password, plain)


# ─── JWT ──────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data          : payload dict (must include 'sub' = user_id)
        expires_delta : custom expiry (defaults to EXPIRE_MINUTES)

    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"[Auth] Token created for sub={data.get('sub')}")
    return token


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT token.

    Returns:
        Payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"[Auth] Token decode failed: {e}")
        return None
