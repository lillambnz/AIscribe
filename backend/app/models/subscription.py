"""Subscription and billing models."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class SubscriptionPlan(Base):
    """Subscription plan definitions."""

    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Solo, Small, Medium, Enterprise
    display_name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    price_monthly = Column(Float, nullable=False)
    price_annual = Column(Float, nullable=True)
    hours_included = Column(Integer, nullable=False)
    max_users = Column(Integer, nullable=True)  # Null = unlimited
    max_storage_gb = Column(Integer, nullable=True)
    features = Column(JSON, nullable=False)  # ["soap_notes", "api_access", "custom_templates"]
    stripe_price_id = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan {self.name} - ${self.price_monthly}/mo>"


class Subscription(Base):
    """Clinic subscriptions."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, unique=True, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active, suspended, cancelled, trialing
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)

    # Stripe integration
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    clinic = relationship("Clinic", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    usage_records = relationship("UsageRecord", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription Clinic {self.clinic_id} - {self.status}>"


class UsageRecord(Base):
    """Track usage for billing."""

    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    period_month = Column(String(7), nullable=False, index=True)  # YYYY-MM

    # Usage metrics
    hours_used = Column(Float, default=0.0, nullable=False)
    encounters_count = Column(Integer, default=0, nullable=False)
    storage_gb = Column(Float, default=0.0, nullable=False)
    api_calls = Column(Integer, default=0, nullable=False)

    # Billing
    overage_hours = Column(Float, default=0.0, nullable=False)
    overage_charge = Column(Float, default=0.0, nullable=False)
    billed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")

    def __repr__(self):
        return f"<UsageRecord {self.period_month} - {self.hours_used}h>"


class Invoice(Base):
    """Invoice records."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)

    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # draft, open, paid, void, uncollectible
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="AUD", nullable=False)

    # Stripe
    stripe_invoice_id = Column(String(255), nullable=True, index=True)

    # Dates
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - ${self.amount_due}>"
