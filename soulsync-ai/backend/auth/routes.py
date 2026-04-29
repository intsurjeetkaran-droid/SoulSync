"""
SoulSync AI - Auth API Routes
POST /auth/signup  → create account
POST /auth/login   → get JWT token
GET  /auth/me      → get current user (protected)
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, field_validator

from backend.auth.models       import get_user_by_email, get_user_by_id
from backend.auth.security     import (
    hash_password_async, verify_password_async, create_access_token
)
from backend.auth.dependencies import get_current_user

logger = logging.getLogger("soulsync.auth.routes")
router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────

class SignupRequest(BaseModel):
    name     : str
    email    : EmailStr
    password : str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email    : EmailStr
    password : str


class AuthResponse(BaseModel):
    access_token : str
    token_type   : str = "bearer"
    user         : dict


# ─── POST /auth/signup ────────────────────────────────────

@router.post("/auth/signup", response_model=AuthResponse, status_code=201)
async def signup(request: SignupRequest):
    """
    Create a new user account.
    Returns JWT token immediately (auto-login after signup).
    bcrypt runs in thread pool — does not block the event loop.
    """
    # Check duplicate email (fast DB query)
    if get_user_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Hash password in thread pool (bcrypt is CPU-intensive)
    hashed = await hash_password_async(request.password)

    # Create user in DB
    try:
        import re, time
        from backend.memory.database import get_connection, get_cursor
        from backend.memory.memory_manager import ensure_user_exists

        safe_prefix = re.sub(r'[^a-z0-9]', '_', request.email.split('@')[0].lower())
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
                (user_id, request.name, request.email.lower().strip(), hashed)
            )
            row = cur.fetchone()
            conn.commit()
            user = dict(row)
        finally:
            cur.close()
            conn.close()

        logger.info(f"[Auth] Signup: {request.email} → {user_id}")

    except Exception as e:
        logger.error(f"[Auth] Signup error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")

    token = create_access_token({"sub": user["user_id"], "name": user["name"]})

    return AuthResponse(
        access_token = token,
        user = {
            "user_id"   : user["user_id"],
            "name"      : user["name"],
            "email"     : user["email"],
            "created_at": str(user["created_at"]),
        }
    )


# ─── POST /auth/login ─────────────────────────────────────

@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Authenticate with email + password.
    bcrypt verify runs in thread pool — does not block the event loop.
    """
    # Fast DB lookup first
    user = get_user_by_email(request.email)
    if not user:
        # Use constant-time response to prevent email enumeration
        await asyncio.sleep(0.1)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    stored_hash = user.get("password")
    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has no password set. Please sign up again.",
        )

    # bcrypt verify in thread pool — this is the slow step
    valid = await verify_password_async(request.password, stored_hash)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Strip password from response
    user.pop("password", None)
    logger.info(f"[Auth] Login success: {request.email}")

    token = create_access_token({"sub": user["user_id"], "name": user["name"]})

    return AuthResponse(
        access_token = token,
        user = {
            "user_id"   : user["user_id"],
            "name"      : user["name"],
            "email"     : user["email"],
            "created_at": str(user["created_at"]),
        }
    )


# ─── GET /auth/me ─────────────────────────────────────────

@router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    Requires: Authorization: Bearer <token>
    """
    return {
        "user_id"   : current_user["user_id"],
        "name"      : current_user["name"],
        "email"     : current_user["email"],
        "created_at": str(current_user["created_at"]),
    }
