"""
SoulSync AI - Auth Dependencies (MongoDB-backed)
FastAPI dependency for JWT-protected routes.
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.auth.security import decode_access_token

logger = logging.getLogger("soulsync.auth.deps")
bearer  = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token payload.")

    # Fetch from MongoDB
    from backend.db.mongo.connection import get_mongo_db
    db = get_mongo_db()
    doc = await db.users.find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User no longer exists.")

    return {
        "user_id"   : doc["user_id"],
        "name"      : doc.get("name", ""),
        "email"     : doc.get("email", ""),
        "created_at": str(doc.get("created_at", "")),
    }


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
) -> dict | None:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
