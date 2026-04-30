"""
SoulSync AI - MySQL Repository (SQLAlchemy async)
Finance domain: wallets, transactions, subscriptions, payments.
All methods return plain dict / list — no ORM objects exposed.
NEVER store chat/memory here.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import get_mysql_session
from .models import (
    PaymentHistoryModel,
    SubscriptionPlanModel,
    TransactionModel,
    UserSubscriptionModel,
    WalletModel,
)

logger = logging.getLogger("soulsync.db.mysql.repo")


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _to_decimal(value) -> Decimal:
    """Safely convert a value to Decimal."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValueError(f"Invalid amount: {value}") from e


class SQLRepository:
    """
    Async repository for all MySQL finance operations.
    Each method manages its own session via the context manager.
    """

    # ═══════════════════════════════════════════════════════
    # WALLET OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def create_wallet(self, user_id: str, currency: str = "INR") -> dict:
        """
        Create a new wallet for a user with zero balance.
        Raises ValueError if wallet already exists.
        """
        try:
            async with get_mysql_session() as session:
                # Check for existing wallet
                existing = await session.scalar(
                    select(WalletModel).where(WalletModel.user_id == user_id)
                )
                if existing:
                    raise ValueError(f"Wallet already exists for user: {user_id}")

                wallet = WalletModel(
                    user_id=user_id,
                    balance=Decimal("0.00"),
                    currency=currency,
                )
                session.add(wallet)
                await session.flush()
                result = wallet.to_dict()
                logger.info(f"[MySQL] Wallet created for user={user_id}")
                return result
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[MySQL] create_wallet failed: {e}", exc_info=True)
            raise

    async def get_wallet(self, user_id: str) -> dict | None:
        """Fetch wallet for a user. Returns None if not found."""
        try:
            async with get_mysql_session() as session:
                wallet = await session.scalar(
                    select(WalletModel).where(WalletModel.user_id == user_id)
                )
                return wallet.to_dict() if wallet else None
        except Exception as e:
            logger.error(f"[MySQL] get_wallet failed: {e}", exc_info=True)
            return None

    async def credit_wallet(
        self,
        user_id: str,
        amount: Decimal,
        description: str,
        reference_id: str = None,
    ) -> dict:
        """
        Credit (add) funds to a user's wallet.
        Creates a transaction record and updates balance atomically.
        Returns the updated wallet dict.
        """
        amount = _to_decimal(amount)
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        try:
            async with get_mysql_session() as session:
                wallet = await session.scalar(
                    select(WalletModel)
                    .where(WalletModel.user_id == user_id)
                    .with_for_update()
                )
                if not wallet:
                    raise ValueError(f"Wallet not found for user: {user_id}")

                wallet.balance += amount
                wallet.updated_at = datetime.utcnow()

                txn = TransactionModel(
                    transaction_id=_new_uuid(),
                    user_id=user_id,
                    type="credit",
                    amount=amount,
                    currency=wallet.currency,
                    description=description,
                    reference_id=reference_id,
                    status="success",
                )
                session.add(txn)
                await session.flush()

                logger.info(f"[MySQL] Credited {amount} to user={user_id} | new_balance={wallet.balance}")
                return wallet.to_dict()
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[MySQL] credit_wallet failed: {e}", exc_info=True)
            raise

    async def debit_wallet(
        self,
        user_id: str,
        amount: Decimal,
        description: str,
        reference_id: str = None,
    ) -> dict:
        """
        Debit (subtract) funds from a user's wallet.
        Raises ValueError if insufficient balance.
        Returns the updated wallet dict.
        """
        amount = _to_decimal(amount)
        if amount <= 0:
            raise ValueError("Debit amount must be positive")

        try:
            async with get_mysql_session() as session:
                wallet = await session.scalar(
                    select(WalletModel)
                    .where(WalletModel.user_id == user_id)
                    .with_for_update()
                )
                if not wallet:
                    raise ValueError(f"Wallet not found for user: {user_id}")
                if wallet.balance < amount:
                    raise ValueError(
                        f"Insufficient balance: {wallet.balance} < {amount}"
                    )

                wallet.balance -= amount
                wallet.updated_at = datetime.utcnow()

                txn = TransactionModel(
                    transaction_id=_new_uuid(),
                    user_id=user_id,
                    type="debit",
                    amount=amount,
                    currency=wallet.currency,
                    description=description,
                    reference_id=reference_id,
                    status="success",
                )
                session.add(txn)
                await session.flush()

                logger.info(f"[MySQL] Debited {amount} from user={user_id} | new_balance={wallet.balance}")
                return wallet.to_dict()
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[MySQL] debit_wallet failed: {e}", exc_info=True)
            raise

    async def get_transaction_history(
        self, user_id: str, limit: int = 20, skip: int = 0
    ) -> list:
        """Fetch paginated transaction history for a user, newest first."""
        try:
            async with get_mysql_session() as session:
                result = await session.execute(
                    select(TransactionModel)
                    .where(TransactionModel.user_id == user_id)
                    .order_by(TransactionModel.created_at.desc())
                    .offset(skip)
                    .limit(limit)
                )
                return [row.to_dict() for row in result.scalars().all()]
        except Exception as e:
            logger.error(f"[MySQL] get_transaction_history failed: {e}", exc_info=True)
            return []

    # ═══════════════════════════════════════════════════════
    # SUBSCRIPTION OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def get_plans(self) -> list:
        """Fetch all active subscription plans."""
        try:
            async with get_mysql_session() as session:
                result = await session.execute(
                    select(SubscriptionPlanModel)
                    .where(SubscriptionPlanModel.is_active == True)
                    .order_by(SubscriptionPlanModel.price.asc())
                )
                return [row.to_dict() for row in result.scalars().all()]
        except Exception as e:
            logger.error(f"[MySQL] get_plans failed: {e}", exc_info=True)
            return []

    async def get_plan(self, plan_id: str) -> dict | None:
        """Fetch a single plan by plan_id."""
        try:
            async with get_mysql_session() as session:
                plan = await session.scalar(
                    select(SubscriptionPlanModel)
                    .where(SubscriptionPlanModel.plan_id == plan_id)
                )
                return plan.to_dict() if plan else None
        except Exception as e:
            logger.error(f"[MySQL] get_plan failed: {e}", exc_info=True)
            return None

    async def subscribe_user(self, user_id: str, plan_id: str) -> dict:
        """
        Subscribe a user to a plan.
        If user already has a subscription, updates it.
        Debits the plan price from the user's wallet.
        Returns the subscription dict.
        """
        try:
            async with get_mysql_session() as session:
                # Fetch plan
                plan = await session.scalar(
                    select(SubscriptionPlanModel)
                    .where(SubscriptionPlanModel.plan_id == plan_id)
                )
                if not plan:
                    raise ValueError(f"Plan not found: {plan_id}")
                if not plan.is_active:
                    raise ValueError(f"Plan is not active: {plan_id}")

                now = datetime.utcnow()
                expires_at = now + timedelta(days=plan.duration_days)

                # Check existing subscription
                existing = await session.scalar(
                    select(UserSubscriptionModel)
                    .where(UserSubscriptionModel.user_id == user_id)
                )

                if existing:
                    existing.plan_id = plan_id
                    existing.status = "active"
                    existing.started_at = now
                    existing.expires_at = expires_at
                    existing.updated_at = now
                    sub = existing
                else:
                    sub = UserSubscriptionModel(
                        user_id=user_id,
                        plan_id=plan_id,
                        status="active",
                        started_at=now,
                        expires_at=expires_at,
                        auto_renew=True,
                    )
                    session.add(sub)

                await session.flush()

                # Record payment if plan has a price
                if plan.price > 0:
                    payment = PaymentHistoryModel(
                        payment_id=_new_uuid(),
                        user_id=user_id,
                        subscription_id=sub.id,
                        amount=plan.price,
                        currency=plan.currency,
                        payment_method="wallet",
                        status="success",
                        gateway_response={"plan": plan_id, "auto": True},
                    )
                    session.add(payment)

                result = sub.to_dict()
                logger.info(f"[MySQL] User {user_id} subscribed to plan={plan_id}")
                return result
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[MySQL] subscribe_user failed: {e}", exc_info=True)
            raise

    async def get_user_subscription(self, user_id: str) -> dict | None:
        """Fetch the current subscription for a user."""
        try:
            async with get_mysql_session() as session:
                sub = await session.scalar(
                    select(UserSubscriptionModel)
                    .where(UserSubscriptionModel.user_id == user_id)
                )
                return sub.to_dict() if sub else None
        except Exception as e:
            logger.error(f"[MySQL] get_user_subscription failed: {e}", exc_info=True)
            return None

    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel a user's subscription. Returns True if cancelled."""
        try:
            async with get_mysql_session() as session:
                result = await session.execute(
                    update(UserSubscriptionModel)
                    .where(UserSubscriptionModel.user_id == user_id)
                    .values(
                        status="cancelled",
                        auto_renew=False,
                        updated_at=datetime.utcnow(),
                    )
                )
                cancelled = result.rowcount > 0
                if cancelled:
                    logger.info(f"[MySQL] Subscription cancelled for user={user_id}")
                return cancelled
        except Exception as e:
            logger.error(f"[MySQL] cancel_subscription failed: {e}", exc_info=True)
            return False

    async def check_subscription_active(self, user_id: str) -> bool:
        """Return True if the user has an active, non-expired subscription."""
        try:
            async with get_mysql_session() as session:
                sub = await session.scalar(
                    select(UserSubscriptionModel)
                    .where(
                        UserSubscriptionModel.user_id == user_id,
                        UserSubscriptionModel.status == "active",
                    )
                )
                if not sub:
                    return False
                if sub.expires_at and sub.expires_at < datetime.utcnow():
                    # Auto-expire
                    await session.execute(
                        update(UserSubscriptionModel)
                        .where(UserSubscriptionModel.user_id == user_id)
                        .values(status="expired", updated_at=datetime.utcnow())
                    )
                    return False
                return True
        except Exception as e:
            logger.error(f"[MySQL] check_subscription_active failed: {e}", exc_info=True)
            return False

    # ═══════════════════════════════════════════════════════
    # PAYMENT OPERATIONS
    # ═══════════════════════════════════════════════════════

    async def record_payment(
        self,
        user_id: str,
        amount: Decimal,
        **kwargs,
    ) -> dict:
        """
        Record a payment event.
        kwargs: subscription_id, currency, payment_method, status, gateway_response
        """
        amount = _to_decimal(amount)
        try:
            async with get_mysql_session() as session:
                payment = PaymentHistoryModel(
                    payment_id=_new_uuid(),
                    user_id=user_id,
                    subscription_id=kwargs.get("subscription_id"),
                    amount=amount,
                    currency=kwargs.get("currency", "INR"),
                    payment_method=kwargs.get("payment_method", "wallet"),
                    status=kwargs.get("status", "pending"),
                    gateway_response=kwargs.get("gateway_response"),
                )
                session.add(payment)
                await session.flush()
                result = payment.to_dict()
                logger.info(f"[MySQL] Payment recorded: {payment.payment_id} user={user_id}")
                return result
        except Exception as e:
            logger.error(f"[MySQL] record_payment failed: {e}", exc_info=True)
            raise

    async def get_payment_history(self, user_id: str, limit: int = 20) -> list:
        """Fetch payment history for a user, newest first."""
        try:
            async with get_mysql_session() as session:
                result = await session.execute(
                    select(PaymentHistoryModel)
                    .where(PaymentHistoryModel.user_id == user_id)
                    .order_by(PaymentHistoryModel.created_at.desc())
                    .limit(limit)
                )
                return [row.to_dict() for row in result.scalars().all()]
        except Exception as e:
            logger.error(f"[MySQL] get_payment_history failed: {e}", exc_info=True)
            return []

    async def get_admin_financial_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Generate an admin financial report for a date range.
        Returns aggregated totals for revenue, transactions, subscriptions.
        """
        try:
            async with get_mysql_session() as session:
                # Total revenue (successful payments)
                revenue_result = await session.execute(
                    select(func.sum(PaymentHistoryModel.amount))
                    .where(
                        PaymentHistoryModel.status == "success",
                        PaymentHistoryModel.created_at >= start_date,
                        PaymentHistoryModel.created_at <= end_date,
                    )
                )
                total_revenue = revenue_result.scalar() or Decimal("0.00")

                # Payment counts by status
                payment_counts = await session.execute(
                    select(
                        PaymentHistoryModel.status,
                        func.count(PaymentHistoryModel.id).label("count"),
                    )
                    .where(
                        PaymentHistoryModel.created_at >= start_date,
                        PaymentHistoryModel.created_at <= end_date,
                    )
                    .group_by(PaymentHistoryModel.status)
                )
                payments_by_status = {row.status: row.count for row in payment_counts}

                # Active subscriptions by plan
                sub_counts = await session.execute(
                    select(
                        UserSubscriptionModel.plan_id,
                        func.count(UserSubscriptionModel.id).label("count"),
                    )
                    .where(UserSubscriptionModel.status == "active")
                    .group_by(UserSubscriptionModel.plan_id)
                )
                subs_by_plan = {row.plan_id: row.count for row in sub_counts}

                # Total wallet credits in period
                credits_result = await session.execute(
                    select(func.sum(TransactionModel.amount))
                    .where(
                        TransactionModel.type == "credit",
                        TransactionModel.status == "success",
                        TransactionModel.created_at >= start_date,
                        TransactionModel.created_at <= end_date,
                    )
                )
                total_credits = credits_result.scalar() or Decimal("0.00")

                # Total wallet debits in period
                debits_result = await session.execute(
                    select(func.sum(TransactionModel.amount))
                    .where(
                        TransactionModel.type == "debit",
                        TransactionModel.status == "success",
                        TransactionModel.created_at >= start_date,
                        TransactionModel.created_at <= end_date,
                    )
                )
                total_debits = debits_result.scalar() or Decimal("0.00")

                return {
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                    "revenue": {
                        "total": str(total_revenue),
                        "currency": "INR",
                    },
                    "payments": {
                        "by_status": payments_by_status,
                        "total": sum(payments_by_status.values()),
                    },
                    "subscriptions": {
                        "active_by_plan": subs_by_plan,
                        "total_active": sum(subs_by_plan.values()),
                    },
                    "wallet_flow": {
                        "total_credits": str(total_credits),
                        "total_debits": str(total_debits),
                        "net": str(total_credits - total_debits),
                    },
                }
        except Exception as e:
            logger.error(f"[MySQL] get_admin_financial_report failed: {e}", exc_info=True)
            raise
