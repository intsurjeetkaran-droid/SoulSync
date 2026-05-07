"""
SoulSync AI - Authentication API Routes (MongoDB-backed)
=========================================================

Complete authentication system with user registration, login, and profile management.
All user data is stored in MongoDB with bcrypt password hashing for security.

Endpoints:
    POST /auth/signup  → Create new user account (returns JWT token)
    POST /auth/login   → Authenticate user and return JWT token
    GET  /auth/me      → Get current authenticated user profile

Security Features:
    - Password hashing with bcrypt (cost factor 12)
    - JWT tokens with configurable expiration (default: 7 days)
    - Email uniqueness validation
    - Password strength requirements (minimum 6 characters)
    - Timing attack mitigation on login

User ID Generation:
    User IDs are generated from email prefix + timestamp to be:
    - Unique (timestamp component)
    - Readable (email-based prefix)
    - URL-safe (special characters replaced with underscores)

Usage:
    # Signup
    POST /api/v1/auth/signup
    {
        "name": "Rohit Sharma",
        "email": "rohit@example.com",
        "password": "securepass123"
    }
    
    # Login
    POST /api/v1/auth/login
    {
        "email": "rohit@example.com",
        "password": "securepass123"
    }
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, field_validator

from backend.auth.security import hash_password_async, verify_password_async, create_access_token
from backend.auth.dependencies import get_current_user

logger = logging.getLogger("soulsync.auth.routes")
router = APIRouter()


def _get_db():
    """
    Get the MongoDB database connection.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


# ─── Request/Response Schemas ────────────────────────────────────────────

class SignupRequest(BaseModel):
    """
    User registration request schema.
    
    Validates that name is not empty and password meets minimum requirements.
    """
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        """Ensure name is not empty or whitespace-only."""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        """Ensure password meets minimum length requirement."""
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response schema with JWT token and user info."""
    access_token: str
    token_type: str = "bearer"
    user: dict


# ─── POST /auth/signup ───────────────────────────────────────────────────

@router.post("/auth/signup", response_model=AuthResponse, status_code=201)
async def signup(request: SignupRequest):
    """
    Create a new user account.
    
    This endpoint:
    1. Validates email is not already registered
    2. Hashes password with bcrypt
    3. Generates unique user ID from email + timestamp
    4. Creates user document in MongoDB
    5. Returns JWT token for immediate authentication
    
    Args:
        request: SignupRequest with name, email, and password
        
    Returns:
        AuthResponse with access token and user info
        
    Raises:
        HTTPException(400): If email is already registered
        HTTPException(500): If database operation fails
    """
    db = _get_db()
    
    # Normalize email (lowercase, trimmed)
    normalized_email = request.email.lower().strip()
    
    # Check for duplicate email
    existing = await db.users.find_one({"email": normalized_email})
    if existing:
        logger.warning(f"[Auth] Signup attempt with existing email: {normalized_email}")
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    # Hash password with bcrypt
    hashed = await hash_password_async(request.password)
    
    # Generate unique user ID from email prefix + timestamp
    import re
    from datetime import datetime
    
    safe_prefix = re.sub(r'[^a-z0-9]', '_', request.email.split('@')[0].lower())
    user_id = f"{safe_prefix}_{int(asyncio.get_event_loop().time())}"
    
    # Create user document
    now = datetime.utcnow()
    doc = {
        "user_id": user_id,
        "name": request.name,
        "email": normalized_email,
        "password_hash": hashed,
        "profile": {},  # Reserved for future profile data
        "preferences": {},  # Reserved for user preferences
        "created_at": now,
        "updated_at": now,
    }
    
    try:
        await db.users.insert_one(doc)
        logger.info(f"[Auth] Signup successful: {normalized_email} → {user_id}")
    except Exception as e:
        logger.error(f"[Auth] Signup database error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")
    
    # Generate JWT token
    token = create_access_token({"sub": user_id, "name": request.name})
    
    return AuthResponse(
        access_token=token,
        user={
            "user_id": user_id,
            "name": request.name,
            "email": normalized_email,
            "created_at": str(doc["created_at"]),
        }
    )


# ─── POST /auth/login ────────────────────────────────────────────────────

@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    This endpoint:
    1. Looks up user by email
    2. Verifies password with bcrypt
    3. Returns JWT token if credentials are valid
    4. Includes timing delay to prevent timing attacks
    
    Args:
        request: LoginRequest with email and password
        
    Returns:
        AuthResponse with access token and user info
        
    Raises:
        HTTPException(401): If credentials are invalid
    """
    db = _get_db()
    
    # Normalize email
    normalized_email = request.email.lower().strip()
    
    # Look up user
    doc = await db.users.find_one({"email": normalized_email})
    
    if not doc:
        # Add delay to prevent timing attacks (user enumeration)
        await asyncio.sleep(0.1)
        logger.warning(f"[Auth] Login attempt with non-existent email: {normalized_email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Invalid email or password.")
    
    # Check if password hash exists
    stored_hash = doc.get("password_hash", "")
    if not stored_hash:
        logger.error(f"[Auth] User {normalized_email} has no password set")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Account has no password set.")
    
    # Verify password
    valid = await verify_password_async(request.password, stored_hash)
    
    if not valid:
        logger.warning(f"[Auth] Failed login attempt for: {normalized_email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Invalid email or password.")
    
    logger.info(f"[Auth] Login successful: {normalized_email}")
    
    # Generate JWT token
    token = create_access_token({"sub": doc["user_id"], "name": doc.get("name", "")})
    
    return AuthResponse(
        access_token=token,
        user={
            "user_id": doc["user_id"],
            "name": doc.get("name", ""),
            "email": doc["email"],
            "created_at": str(doc.get("created_at", "")),
        }
    )


# ─── GET /auth/me ────────────────────────────────────────────────────────

@router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    
    This endpoint requires a valid JWT token in the Authorization header.
    The token is validated and the user document is retrieved from MongoDB.
    
    Args:
        current_user: Injected by get_current_user dependency
        
    Returns:
        User profile information (user_id, name, email, created_at)
        
    Raises:
        HTTPException(401): If token is missing or invalid
        HTTPException(404): If user not found
    """
    return {
        "user_id": current_user["user_id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "created_at": str(current_user.get("created_at", "")),
    }


# ─── POST /auth/logout ───────────────────────────────────────────────────

@router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user (invalidate token).
    
    Note: Since JWT tokens are stateless, this endpoint doesn't actually
    invalidate the token. In a production system, you would implement
    token blacklisting using Redis or a database table.
    
    Args:
        current_user: Injected by get_current_user dependency
        
    Returns:
        Success message
    """
    logger.info(f"[Auth] Logout: {current_user['email']}")
    return {"message": "Logged out successfully"}