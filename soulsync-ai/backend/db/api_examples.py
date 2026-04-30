"""
SoulSync AI - API Examples (v2)
Shows how the new hybrid db/ services plug into FastAPI.

These are EXAMPLE endpoints — not wired into main.py yet.
To activate, import this router in main.py:
    from backend.db.api_examples import router as v2_router
    app.include_router(v2_router, prefix="/api/v2", tags=["V2 Hybrid"])
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from .mongo.connection import get_mongo_db
from .mongo.repository import MongoRepository
from .mysql.repository import SQLRepository
from .redis.cache import RedisCacheManager
from .services.chat_service import ChatService
from .services.memory_service import MemoryService
from .services.payment_service import PaymentService
from .services.task_service import TaskService
from .services.user_service import UserService

logger = logging.getLogger("soulsync.api.v2")
router = APIRouter()


# ─── Dependency Factories ─────────────────────────────────

def get_mongo_repo() -> MongoRepository:
    """FastAPI dependency: returns a MongoRepository instance."""
    db = get_mongo_db()
    return MongoRepository(db)


def get_sql_repo() -> SQLRepository:
    """FastAPI dependency: returns a SQLRepository instance."""
    return SQLRepository()


def get_redis_cache() -> RedisCacheManager:
    """FastAPI dependency: returns a RedisCacheManager instance."""
    return RedisCacheManager()


def get_chat_service(
    mongo: MongoRepository = Depends(get_mongo_repo),
    cache: RedisCacheManager = Depends(get_redis_cache),
) -> ChatService:
    return ChatService(mongo_repo=mongo, redis_cache=cache)


def get_memory_service(
    mongo: MongoRepository = Depends(get_mongo_repo),
    cache: RedisCacheManager = Depends(get_redis_cache),
) -> MemoryService:
    return MemoryService(mongo_repo=mongo, redis_cache=cache)


def get_task_service(
    mongo: MongoRepository = Depends(get_mongo_repo),
) -> TaskService:
    return TaskService(mongo_repo=mongo)


def get_user_service(
    mongo: MongoRepository = Depends(get_mongo_repo),
    sql: SQLRepository = Depends(get_sql_repo),
) -> UserService:
    return UserService(mongo_repo=mongo, sql_repo=sql)


def get_payment_service(
    sql: SQLRepository = Depends(get_sql_repo),
) -> PaymentService:
    return PaymentService(sql_repo=sql)


# ─── Request / Response Schemas ───────────────────────────

class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None
    use_cache: bool = True


class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str]
    message_id: Optional[str]
    retrieved_memories: list
    intent: str
    tasks_created: list
    cached: bool


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TaskCreateRequest(BaseModel):
    user_id: str
    title: str
    due_date: Optional[str] = None
    priority: str = "medium"


class MemoryStoreRequest(BaseModel):
    user_id: str
    key: str
    value: str
    source_text: Optional[str] = None


class AddCreditsRequest(BaseModel):
    amount: float
    reference: str
    description: str = "Credits added"


class SubscribeRequest(BaseModel):
    plan_id: str


# ─── Chat Endpoints ───────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, summary="Send a message (v2 — MongoDB + Redis)")
async def chat_v2(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """
    Main chat endpoint using the new hybrid architecture.
    - Checks Redis cache first
    - Stores messages in MongoDB
    - Uses FAISS for semantic memory retrieval
    - Calls Groq AI
    - Caches response in Redis
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        result = await service.send_message(
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            use_cache=request.use_cache,
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"[API v2] /chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{user_id}/conversations", summary="List user conversations")
async def get_conversations(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    service: ChatService = Depends(get_chat_service),
):
    """Return recent conversations for a user (cached in Redis)."""
    return await service.get_user_conversations(user_id=user_id, limit=limit)


@router.get("/chat/{conversation_id}/messages", summary="Get conversation messages")
async def get_messages(
    conversation_id: str,
    user_id: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ChatService = Depends(get_chat_service),
):
    """Return paginated messages for a conversation."""
    return await service.get_conversation_history(
        user_id=user_id,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
    )


# ─── Auth Endpoints ───────────────────────────────────────

@router.post("/auth/signup", summary="Register a new user (v2 — MongoDB + MySQL wallet)")
async def signup_v2(
    request: SignupRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Create a new user.
    - Stores profile in MongoDB
    - Creates wallet in MySQL
    """
    try:
        user = await service.create_user(
            name=request.name,
            email=request.email,
            password=request.password,
        )
        return {"status": "created", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"[API v2] /auth/signup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/login", summary="Login (v2 — MongoDB auth)")
async def login_v2(
    request: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    """Authenticate user against MongoDB."""
    user = await service.authenticate(email=request.email, password=request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate JWT token using existing security module
    from backend.auth.security import create_access_token
    token = create_access_token({"sub": user["user_id"]})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/auth/me/{user_id}", summary="Get user profile (v2)")
async def get_profile_v2(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    """Return full user profile including subscription status and wallet balance."""
    try:
        return await service.get_profile(user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── Memory Endpoints ─────────────────────────────────────

@router.post("/memory/store", summary="Store a personal fact (v2 — MongoDB)")
async def store_memory_v2(
    request: MemoryStoreRequest,
    service: MemoryService = Depends(get_memory_service),
):
    """Store a personal fact in MongoDB and invalidate Redis cache."""
    result = await service.store_fact(
        user_id=request.user_id,
        key=request.key,
        value=request.value,
        source_text=request.source_text,
    )
    return {"status": "stored", "fact": result}


@router.get("/memory/{user_id}/facts", summary="Get all memory facts")
async def get_facts_v2(
    user_id: str,
    key: Optional[str] = Query(default=None),
    service: MemoryService = Depends(get_memory_service),
):
    """Return all personal facts for a user, optionally filtered by key."""
    return await service.get_all_facts(user_id=user_id, key=key)


@router.get("/memory/{user_id}/search", summary="Search memories (FAISS + MongoDB)")
async def search_memories_v2(
    user_id: str,
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=5, ge=1, le=20),
    service: MemoryService = Depends(get_memory_service),
):
    """Semantic search using FAISS with MongoDB keyword fallback."""
    return await service.search_memories(user_id=user_id, query=query, top_k=top_k)


# ─── Task Endpoints ───────────────────────────────────────

@router.post("/tasks", summary="Create a task (v2 — MongoDB)")
async def create_task_v2(
    request: TaskCreateRequest,
    service: TaskService = Depends(get_task_service),
):
    """Create a new task in MongoDB."""
    task = await service.create_task(
        user_id=request.user_id,
        title=request.title,
        due_date=request.due_date,
        priority=request.priority,
    )
    return {"status": "created", "task": task}


@router.get("/tasks/{user_id}", summary="Get tasks for a user")
async def get_tasks_v2(
    user_id: str,
    status: Optional[str] = Query(default=None, pattern="^(pending|completed)$"),
    service: TaskService = Depends(get_task_service),
):
    """Return tasks for a user, optionally filtered by status."""
    return await service.get_tasks(user_id=user_id, status=status)


@router.patch("/tasks/{task_id}/complete", summary="Complete a task")
async def complete_task_v2(
    task_id: str,
    user_id: str = Query(...),
    service: TaskService = Depends(get_task_service),
):
    """Mark a task as completed."""
    result = await service.complete_task(task_id=task_id, user_id=user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/tasks/{task_id}", summary="Delete a task")
async def delete_task_v2(
    task_id: str,
    user_id: str = Query(...),
    service: TaskService = Depends(get_task_service),
):
    """Delete a task."""
    deleted = await service.delete_task(task_id=task_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "task_id": task_id}


# ─── Payment / Wallet Endpoints ───────────────────────────

@router.get("/wallet/{user_id}", summary="Get wallet (v2 — MySQL)")
async def get_wallet_v2(
    user_id: str,
    service: PaymentService = Depends(get_payment_service),
):
    """Return wallet balance and details for a user."""
    return await service.get_wallet(user_id=user_id)


@router.post("/wallet/{user_id}/credit", summary="Add credits to wallet")
async def add_credits_v2(
    user_id: str,
    request: AddCreditsRequest,
    service: PaymentService = Depends(get_payment_service),
):
    """Credit funds to a user's wallet."""
    try:
        wallet = await service.add_credits(
            user_id=user_id,
            amount=Decimal(str(request.amount)),
            reference=request.reference,
            description=request.description,
        )
        return {"status": "credited", "wallet": wallet}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallet/{user_id}/transactions", summary="Get transaction history")
async def get_transactions_v2(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: PaymentService = Depends(get_payment_service),
):
    """Return paginated transaction history for a user."""
    return await service.get_transaction_history(
        user_id=user_id, page=page, page_size=page_size
    )


@router.get("/subscriptions/plans", summary="List available subscription plans")
async def get_plans_v2(
    service: PaymentService = Depends(get_payment_service),
):
    """Return all active subscription plans."""
    return await service.get_available_plans()


@router.post("/subscriptions/{user_id}/subscribe", summary="Subscribe to a plan")
async def subscribe_v2(
    user_id: str,
    request: SubscribeRequest,
    service: PaymentService = Depends(get_payment_service),
):
    """Subscribe a user to a plan (deducts from wallet if price > 0)."""
    try:
        subscription = await service.subscribe(user_id=user_id, plan_id=request.plan_id)
        return {"status": "subscribed", "subscription": subscription}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions/{user_id}", summary="Get user subscription")
async def get_subscription_v2(
    user_id: str,
    service: PaymentService = Depends(get_payment_service),
):
    """Return the current subscription for a user."""
    sub = await service.get_subscription(user_id=user_id)
    if not sub:
        return {"subscription": None, "active": False}
    active = await service.is_subscribed(user_id=user_id)
    return {"subscription": sub, "active": active}


@router.delete("/subscriptions/{user_id}", summary="Cancel subscription")
async def cancel_subscription_v2(
    user_id: str,
    service: PaymentService = Depends(get_payment_service),
):
    """Cancel a user's subscription."""
    cancelled = await service.cancel_subscription(user_id=user_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return {"status": "cancelled"}


@router.get("/admin/financial-report", summary="Admin financial report (MySQL)")
async def admin_report_v2(
    start_date: str = Query(..., description="ISO date: 2026-01-01"),
    end_date: str = Query(..., description="ISO date: 2026-01-31"),
    service: PaymentService = Depends(get_payment_service),
):
    """Generate an admin financial report for a date range."""
    try:
        return await service.admin_financial_report(
            start_date=start_date, end_date=end_date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
