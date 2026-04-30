"""
SoulSync AI - User Service (MongoDB-only)
All user data lives in MongoDB.
MySQL wallet/subscription calls are removed — PaymentService handles those when re-enabled.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from ..mongo.repository import MongoRepository

logger = logging.getLogger("soulsync.services.user")


class UserService:
    """User management service — MongoDB only."""

    def __init__(self, mongo_repo: MongoRepository):
        self.mongo = mongo_repo

    async def create_user(self, name: str, email: str, password: str) -> dict:
        existing = await self.mongo.get_user_by_email(email)
        if existing:
            raise ValueError(f"Email already registered: {email}")

        from backend.auth.security import hash_password
        password_hash = hash_password(password)

        safe_prefix = re.sub(r"[^a-z0-9]", "_", email.split("@")[0].lower())
        user_id = f"{safe_prefix}_{int(time.time())}"

        user_data = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "profile": {},
            "preferences": {},
        }
        user_doc = await self.mongo.create_user(user_data)
        logger.info(f"[UserService] User created: {email} → {user_id}")
        return user_doc

    async def authenticate(self, email: str, password: str) -> dict | None:
        user = await self.mongo.get_user_with_password(email)
        if not user:
            return None
        from backend.auth.security import verify_password
        if not verify_password(password, user.get("password_hash", "")):
            return None
        user.pop("password_hash", None)
        return user

    async def get_profile(self, user_id: str) -> dict:
        user = await self.mongo.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        return {
            **user,
            "subscription_active": False,
            "subscription": None,
            "wallet_balance": "0.00",
        }

    async def update_profile(self, user_id: str, updates: dict) -> bool:
        return await self.mongo.update_user_profile(user_id, updates)

    async def get_user_by_email(self, email: str) -> dict | None:
        user = await self.mongo.get_user_by_email(email)
        if user:
            user.pop("password_hash", None)
        return user

    async def get_user_by_id(self, user_id: str) -> dict | None:
        return await self.mongo.get_user_by_id(user_id)

    async def ensure_user_exists(self, user_id: str, name: Optional[str] = None) -> dict:
        user = await self.mongo.get_user_by_id(user_id)
        if user:
            return user
        try:
            user_data = {
                "user_id": user_id,
                "name": name or user_id,
                "email": f"{user_id}@legacy.soulsync.ai",
                "password_hash": "",
                "profile": {},
                "preferences": {},
            }
            user = await self.mongo.create_user(user_data)
            logger.info(f"[UserService] Auto-created legacy user: {user_id}")
            return user
        except Exception as e:
            logger.warning(f"[UserService] ensure_user_exists failed: {e}")
            return {"user_id": user_id, "name": name or user_id}
