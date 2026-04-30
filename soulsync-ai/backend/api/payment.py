"""
SoulSync AI - Payment API Router (DISABLED)
All endpoints return a "coming soon" response.
MySQL will be re-enabled here when payments are implemented.
"""

from fastapi import APIRouter

router = APIRouter()

_DISABLED = {"status": "disabled", "message": "Payment system coming soon!"}


@router.get("/payments/wallet/{user_id}")
async def get_wallet(user_id: str):
    return _DISABLED


@router.post("/payments/subscribe")
async def subscribe():
    return _DISABLED


@router.get("/payments/plans")
async def get_plans():
    return {**_DISABLED, "plans": []}


@router.get("/payments/subscription/{user_id}")
async def get_subscription(user_id: str):
    return _DISABLED


@router.delete("/payments/subscription/{user_id}")
async def cancel_subscription(user_id: str):
    return _DISABLED


@router.get("/payments/transactions/{user_id}")
async def get_transactions(user_id: str):
    return {**_DISABLED, "transactions": []}


@router.get("/payments/history/{user_id}")
async def get_payment_history(user_id: str):
    return {**_DISABLED, "history": []}
