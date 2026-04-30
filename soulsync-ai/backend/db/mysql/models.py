"""
SoulSync AI - MySQL SQLAlchemy ORM Models
Finance domain: wallets, transactions, subscriptions, payments.
NEVER store chat/memory here — that belongs in MongoDB.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Shared declarative base for all MySQL models."""
    pass


# ─── Wallet ───────────────────────────────────────────────

class WalletModel(Base):
    """
    One wallet per user.
    Stores current balance and currency.
    """
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    # Relationships
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="wallet", lazy="select"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": str(self.balance),
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Transaction ──────────────────────────────────────────

class TransactionModel(Base):
    """
    Immutable ledger of all wallet credits and debits.
    """
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, default=_new_uuid, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("wallets.user_id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)   # credit / debit
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reference_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    wallet: Mapped["WalletModel"] = relationship("WalletModel", back_populates="transactions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "type": self.type,
            "amount": str(self.amount),
            "currency": self.currency,
            "description": self.description,
            "reference_id": self.reference_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── Subscription Plan ────────────────────────────────────

class SubscriptionPlanModel(Base):
    """
    Available subscription plans (Free, Pro, Premium, etc.).
    Managed by admins; users subscribe to these.
    """
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, default=_new_uuid, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    subscriptions: Mapped[list["UserSubscriptionModel"]] = relationship(
        "UserSubscriptionModel", back_populates="plan", lazy="select"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "name": self.name,
            "price": str(self.price),
            "currency": self.currency,
            "duration_days": self.duration_days,
            "features": self.features or {},
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── User Subscription ────────────────────────────────────

class UserSubscriptionModel(Base):
    """
    Active subscription for a user.
    One active subscription per user at a time.
    """
    __tablename__ = "user_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_subscription"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("subscription_plans.plan_id", ondelete="RESTRICT"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active / expired / cancelled
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    # Relationship
    plan: Mapped["SubscriptionPlanModel"] = relationship(
        "SubscriptionPlanModel", back_populates="subscriptions"
    )
    payments: Mapped[list["PaymentHistoryModel"]] = relationship(
        "PaymentHistoryModel", back_populates="subscription", lazy="select"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auto_renew": self.auto_renew,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Payment History ──────────────────────────────────────

class PaymentHistoryModel(Base):
    """
    Immutable record of every payment attempt.
    Linked to a user subscription.
    """
    __tablename__ = "payment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, default=_new_uuid, index=True
    )
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user_subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="wallet")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # success / failed / pending
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    subscription: Mapped[Optional["UserSubscriptionModel"]] = relationship(
        "UserSubscriptionModel", back_populates="payments"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "subscription_id": self.subscription_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "payment_method": self.payment_method,
            "status": self.status,
            "gateway_response": self.gateway_response or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
