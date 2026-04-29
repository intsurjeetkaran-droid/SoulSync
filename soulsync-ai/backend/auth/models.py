"""
SoulSync AI - Auth DB Models
User CRUD operations against PostgreSQL.
"""

import logging
from datetime import datetime
from backend.memory.database import get_connection, get_cursor
from backend.auth.security   import hash_password, verify_password

logger = logging.getLogger("soulsync.auth.models")


# ─── Schema migration ─────────────────────────────────────

def migrate_auth_schema():
    """
    Add auth columns to the users table if they don't exist.
    Safe to run multiple times.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        # Add email column
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS email    VARCHAR(255) UNIQUE,
            ADD COLUMN IF NOT EXISTS password VARCHAR(255);
        """)
        # Create index on email
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
            ON users(email) WHERE email IS NOT NULL;
        """)
        conn.commit()
        logger.info("[Auth] Schema migration complete")
    except Exception as e:
        conn.rollback()
        logger.error(f"[Auth] Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ─── Create user ──────────────────────────────────────────

def create_user(name: str, email: str, password: str) -> dict:
    """
    Create a new user with hashed password.

    Returns the created user dict (without password).
    Raises ValueError if email already exists.
    """
    # Check duplicate email
    if get_user_by_email(email):
        raise ValueError(f"Email already registered: {email}")

    hashed = hash_password(password)
    # user_id = sanitized email prefix + timestamp for uniqueness
    import re, time
    safe_prefix = re.sub(r'[^a-z0-9]', '_', email.split('@')[0].lower())
    user_id     = f"{safe_prefix}_{int(time.time())}"

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO users (user_id, name, email, password)
            VALUES (%s, %s, %s, %s)
            RETURNING id, user_id, name, email, created_at;
            """,
            (user_id, name, email.lower().strip(), hashed)
        )
        row = cur.fetchone()
        conn.commit()
        result = dict(row)
        logger.info(f"[Auth] User created: {email} → user_id={user_id}")
        return result
    finally:
        cur.close()
        conn.close()


# ─── Get user ─────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    """Fetch user by email. Returns None if not found."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT id, user_id, name, email, password, created_at "
            "FROM users WHERE email = %s;",
            (email.lower().strip(),)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        cur.close()
        conn.close()


def get_user_by_id(user_id: str) -> dict | None:
    """Fetch user by user_id. Returns None if not found."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT id, user_id, name, email, created_at "
            "FROM users WHERE user_id = %s;",
            (user_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        cur.close()
        conn.close()


# ─── Authenticate ─────────────────────────────────────────

def authenticate_user(email: str, password: str) -> dict | None:
    """
    Verify email + password.

    Returns user dict (without password) if valid, None otherwise.
    """
    user = get_user_by_email(email)
    if not user:
        logger.warning(f"[Auth] Login failed — email not found: {email}")
        return None
    if not verify_password(password, user["password"]):
        logger.warning(f"[Auth] Login failed — wrong password: {email}")
        return None
    # Strip password from returned dict
    user.pop("password", None)
    logger.info(f"[Auth] Login success: {email}")
    return user
