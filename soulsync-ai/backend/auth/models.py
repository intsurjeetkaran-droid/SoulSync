"""
SoulSync AI - Auth Models (MongoDB-backed)
User CRUD via MongoDB async Motor client.
PostgreSQL is no longer used for auth.
"""

import logging
import asyncio
from backend.auth.security import hash_password, verify_password

logger = logging.getLogger("soulsync.auth.models")


def _get_mongo_db():
    """Lazy import to avoid circular imports at module load time."""
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


def _run(coro):
    """Run an async coroutine from sync context safely."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ─── Create user ──────────────────────────────────────────

def create_user(name: str, email: str, password: str) -> dict:
    """Create a new user in MongoDB. Raises ValueError if email exists."""
    async def _create():
        db = _get_mongo_db()
        existing = await db.users.find_one({"email": email.lower().strip()})
        if existing:
            raise ValueError(f"Email already registered: {email}")

        import re, time, uuid
        safe_prefix = re.sub(r'[^a-z0-9]', '_', email.split('@')[0].lower())
        user_id = f"{safe_prefix}_{int(time.time())}"
        hashed = hash_password(password)

        doc = {
            "user_id": user_id,
            "name": name,
            "email": email.lower().strip(),
            "password_hash": hashed,
            "profile": {},
            "preferences": {},
            "created_at": __import__("datetime").datetime.utcnow(),
            "updated_at": __import__("datetime").datetime.utcnow(),
        }
        await db.users.insert_one(doc)
        logger.info(f"[Auth] User created: {email} → {user_id}")
        return {
            "user_id": user_id,
            "name": name,
            "email": email.lower().strip(),
            "created_at": str(doc["created_at"]),
        }
    return _run(_create())


# ─── Get user ─────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    """Fetch user by email including password_hash."""
    async def _get():
        db = _get_mongo_db()
        doc = await db.users.find_one({"email": email.lower().strip()})
        if not doc:
            return None
        return {
            "user_id": doc["user_id"],
            "name": doc.get("name", ""),
            "email": doc["email"],
            "password": doc.get("password_hash", ""),  # keep key as 'password' for compat
            "created_at": str(doc.get("created_at", "")),
        }
    return _run(_get())


def get_user_by_id(user_id: str) -> dict | None:
    """Fetch user by user_id (no password)."""
    async def _get():
        db = _get_mongo_db()
        doc = await db.users.find_one({"user_id": user_id})
        if not doc:
            return None
        return {
            "user_id": doc["user_id"],
            "name": doc.get("name", ""),
            "email": doc.get("email", ""),
            "created_at": str(doc.get("created_at", "")),
        }
    return _run(_get())


# ─── Authenticate ─────────────────────────────────────────

def authenticate_user(email: str, password: str) -> dict | None:
    """Verify email + password. Returns user dict or None."""
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.get("password", "")):
        return None
    user.pop("password", None)
    return user


# ─── Schema migration (no-op — MongoDB is schemaless) ─────

def migrate_auth_schema():
    """No-op: MongoDB doesn't need schema migrations."""
    logger.info("[Auth] MongoDB auth — no schema migration needed")
