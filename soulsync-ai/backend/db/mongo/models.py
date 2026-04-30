"""
SoulSync AI - MongoDB Pydantic Document Models
Plain Pydantic v2 models used for validation and serialization.
Motor handles the actual DB operations; these models define the shape.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
import uuid


def _now() -> datetime:
    return datetime.utcnow()


def _new_id() -> str:
    return str(uuid.uuid4())


# ─── User ─────────────────────────────────────────────────

class UserDocument(BaseModel):
    """MongoDB users collection document."""
    user_id: str = Field(default_factory=_new_id)
    name: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    profile: dict[str, Any] = Field(default_factory=dict)
    # e.g. {"age": 25, "location": "Mumbai", "job": "Engineer"}
    preferences: dict[str, Any] = Field(default_factory=dict)
    # e.g. {"language": "en", "voice": "female", "theme": "dark"}

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()

    def to_dict(self) -> dict:
        d = self.model_dump()
        d.pop("password_hash", None)  # never expose hash
        return d


# ─── Conversation ─────────────────────────────────────────

class ConversationDocument(BaseModel):
    """MongoDB conversations collection document."""
    conversation_id: str = Field(default_factory=_new_id)
    user_id: str
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    message_count: int = 0
    last_message_at: datetime = Field(default_factory=_now)

    def to_dict(self) -> dict:
        return self.model_dump()


# ─── Message ──────────────────────────────────────────────

class MessageDocument(BaseModel):
    """MongoDB messages collection document."""
    message_id: str = Field(default_factory=_new_id)
    conversation_id: str
    user_id: str
    role: str  # 'user' or 'assistant'
    content: str
    importance_score: int = 5
    emotion: str = "neutral"
    intent: str = "normal_chat"
    created_at: datetime = Field(default_factory=_now)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return v

    def to_dict(self) -> dict:
        return self.model_dump()


# ─── Memory (Personal Facts) ──────────────────────────────

class MemoryDocument(BaseModel):
    """
    MongoDB memories collection document.
    Stores structured personal facts: name, goal, job, etc.
    """
    memory_id: str = Field(default_factory=_new_id)
    user_id: str
    key: str          # 'name', 'goal', 'job', 'hobby', etc.
    value: str
    context: str = "general"   # 'identity', 'goal', 'preference', 'career'
    source_text: Optional[str] = None
    event_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    def to_dict(self) -> dict:
        return self.model_dump()


# ─── Task ─────────────────────────────────────────────────

class TaskDocument(BaseModel):
    """MongoDB tasks collection document."""
    task_id: str = Field(default_factory=_new_id)
    user_id: str
    title: str
    due_date: Optional[str] = None
    priority: str = "medium"   # high / medium / low
    status: str = "pending"    # pending / completed
    source: str = "manual"     # manual / auto
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    completed_at: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in ("high", "medium", "low"):
            raise ValueError("priority must be high, medium, or low")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("pending", "completed"):
            raise ValueError("status must be pending or completed")
        return v

    def to_dict(self) -> dict:
        return self.model_dump()


# ─── Activity ─────────────────────────────────────────────

class ActivityDocument(BaseModel):
    """MongoDB activities collection document."""
    activity_id: str = Field(default_factory=_new_id)
    user_id: str
    raw_text: str
    emotion: str = "neutral"
    activity: str = ""
    status: str = ""
    productivity: str = ""
    summary: str = ""
    created_at: datetime = Field(default_factory=_now)

    def to_dict(self) -> dict:
        return self.model_dump()


# ─── Mood Log ─────────────────────────────────────────────

class MoodLogDocument(BaseModel):
    """MongoDB mood_logs collection document."""
    log_id: str = Field(default_factory=_new_id)
    user_id: str
    mood: str
    mood_score: int = Field(ge=1, le=10)
    note: str = ""
    day_of_week: str = ""    # Monday, Tuesday, etc.
    hour_of_day: int = 0     # 0-23
    source: str = "manual"   # manual / auto
    created_at: datetime = Field(default_factory=_now)

    def to_dict(self) -> dict:
        return self.model_dump()
