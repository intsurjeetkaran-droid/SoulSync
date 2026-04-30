"""
SoulSync AI - Auth API Routes (MongoDB-backed)
POST /auth/signup  → create account in MongoDB
POST /auth/login   → verify against MongoDB, return JWT
GET  /auth/me      → return current user from MongoDB
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, field_validator

from backend.auth.security     import hash_password_async, verify_password_async, create_access_token
from backend.auth.dependencies import get_current_user

logger = logging.getLogger("soulsync.auth.routes")
router = APIRouter()


def _get_db():
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


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
    db = _get_db()

    # Check duplicate email
    existing = await db.users.find_one({"email": request.email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed = await hash_password_async(request.password)

    import re, time
    from datetime import datetime
    safe_prefix = re.sub(r'[^a-z0-9]', '_', request.email.split('@')[0].lower())
    user_id = f"{safe_prefix}_{int(time.time())}"

    doc = {
        "user_id"      : user_id,
        "name"         : request.name,
        "email"        : request.email.lower().strip(),
        "password_hash": hashed,
        "profile"      : {},
        "preferences"  : {},
        "created_at"   : datetime.utcnow(),
        "updated_at"   : datetime.utcnow(),
    }

    try:
        await db.users.insert_one(doc)
        logger.info(f"[Auth] Signup: {request.email} → {user_id}")
    except Exception as e:
        logger.error(f"[Auth] Signup error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")

    token = create_access_token({"sub": user_id, "name": request.name})
    return AuthResponse(
        access_token=token,
        user={
            "user_id"   : user_id,
            "name"      : request.name,
            "email"     : request.email.lower().strip(),
            "created_at": str(doc["created_at"]),
        }
    )


# ─── POST /auth/login ─────────────────────────────────────

@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    db = _get_db()

    doc = await db.users.find_one({"email": request.email.lower().strip()})
    if not doc:
        await asyncio.sleep(0.1)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid email or password.")

    stored_hash = doc.get("password_hash", "")
    if not stored_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Account has no password set.")

    valid = await verify_password_async(request.password, stored_hash)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid email or password.")

    logger.info(f"[Auth] Login success: {request.email}")
    token = create_access_token({"sub": doc["user_id"], "name": doc.get("name", "")})
    return AuthResponse(
        access_token=token,
        user={
            "user_id"   : doc["user_id"],
            "name"      : doc.get("name", ""),
            "email"     : doc["email"],
            "created_at": str(doc.get("created_at", "")),
        }
    )


# ─── GET /auth/me ─────────────────────────────────────────

@router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id"   : current_user["user_id"],
        "name"      : current_user["name"],
        "email"     : current_user["email"],
        "created_at": str(current_user.get("created_at", "")),
    }
