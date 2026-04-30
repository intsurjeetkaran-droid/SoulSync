"""
SoulSync AI - Hybrid Database Layer
MongoDB (Motor) for chat/memory/tasks/logs
MySQL (SQLAlchemy async) for wallet/transactions/subscriptions
Redis for caching
FAISS for vector search (unchanged)
"""

from .config import settings

__all__ = ["settings"]
