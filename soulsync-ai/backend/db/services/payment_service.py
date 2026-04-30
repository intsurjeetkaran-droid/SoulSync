"""
SoulSync AI - Payment Service (DISABLED)
MySQL/payments are not active in this version.
All methods raise NotImplementedError or return a disabled response.

To re-enable:
  1. Set ENABLE_PAYMENTS=True in .env
  2. Configure MySQL credentials in .env
  3. Uncomment the MySQL imports and swap the implementation
"""

from __future__ import annotations
import logging

logger = logging.getLogger("soulsync.services.payment")

PAYMENTS_DISABLED_MSG = {
    "status": "disabled",
    "message": "Payment system is not enabled yet. Coming soon!",
}


class PaymentService:
    """
    Payment service placeholder.
    All methods return a disabled response until MySQL is re-enabled.
    """

    def __init__(self):
        logger.info("[PaymentService] Running in DISABLED mode")

    async def get_wallet(self, user_id: str) -> dict:
        return PAYMENTS_DISABLED_MSG

    async def add_credits(self, user_id: str, amount, reference: str, description: str = "") -> dict:
        return PAYMENTS_DISABLED_MSG

    async def deduct_credits(self, user_id: str, amount, description: str, reference=None) -> dict:
        return PAYMENTS_DISABLED_MSG

    async def subscribe(self, user_id: str, plan_id: str) -> dict:
        return PAYMENTS_DISABLED_MSG

    async def get_subscription(self, user_id: str) -> dict:
        return PAYMENTS_DISABLED_MSG

    async def cancel_subscription(self, user_id: str) -> dict:
        return PAYMENTS_DISABLED_MSG

    async def is_subscribed(self, user_id: str) -> bool:
        return False

    async def get_available_plans(self) -> list:
        return []

    async def get_transaction_history(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        return {"transactions": [], **PAYMENTS_DISABLED_MSG}

    async def get_payment_history(self, user_id: str, limit: int = 20) -> list:
        return []

    async def admin_financial_report(self, start_date: str, end_date: str) -> dict:
        return PAYMENTS_DISABLED_MSG

    async def record_payment(self, user_id: str, amount, **kwargs) -> dict:
        return PAYMENTS_DISABLED_MSG
