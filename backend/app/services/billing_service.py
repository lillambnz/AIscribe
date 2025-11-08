"""Billing and subscription service."""
import time
from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from app.core.config import settings
from app.models.subscription import Subscription, SubscriptionPlan, UsageRecord, Invoice
from app.models.clinic import Clinic


# Initialize Stripe if available
if STRIPE_AVAILABLE and hasattr(settings, 'STRIPE_SECRET_KEY'):
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)


class BillingService:
    """Service for managing subscriptions and billing."""

    OVERAGE_RATE = 2.0  # $2 AUD per hour over limit

    @staticmethod
    async def create_customer(clinic: Clinic, email: str) -> Optional[str]:
        """
        Create Stripe customer.

        Args:
            clinic: Clinic model instance
            email: Customer email

        Returns:
            Stripe customer ID or None if Stripe not configured
        """
        if not STRIPE_AVAILABLE:
            return None

        try:
            customer = stripe.Customer.create(
                email=email,
                name=clinic.name,
                metadata={
                    "clinic_id": clinic.id,
                    "data_residency": clinic.data_residency,
                }
            )
            return customer.id
        except Exception as e:
            print(f"Error creating Stripe customer: {e}")
            return None

    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        clinic_id: int,
        plan_id: int,
        stripe_customer_id: Optional[str] = None,
        trial_days: int = 14,
    ) -> Subscription:
        """
        Create subscription for clinic.

        Args:
            db: Database session
            clinic_id: Clinic ID
            plan_id: Subscription plan ID
            stripe_customer_id: Stripe customer ID
            trial_days: Trial period in days

        Returns:
            Created Subscription
        """
        # Get plan
        plan = await db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise ValueError("Invalid plan ID")

        # Create Stripe subscription if customer ID provided
        stripe_subscription_id = None
        if STRIPE_AVAILABLE and stripe_customer_id and plan.stripe_price_id:
            try:
                stripe_sub = stripe.Subscription.create(
                    customer=stripe_customer_id,
                    items=[{"price": plan.stripe_price_id}],
                    trial_period_days=trial_days,
                    payment_behavior="default_incomplete",
                    payment_settings={"save_default_payment_method": "on_subscription"},
                    expand=["latest_invoice.payment_intent"],
                )
                stripe_subscription_id = stripe_sub.id
            except Exception as e:
                print(f"Error creating Stripe subscription: {e}")

        # Calculate dates
        now = datetime.utcnow()
        trial_ends_at = now + timedelta(days=trial_days) if trial_days > 0 else None
        current_period_start = now
        current_period_end = now + timedelta(days=30)  # Monthly billing

        # Create subscription
        subscription = Subscription(
            clinic_id=clinic_id,
            plan_id=plan_id,
            status="trialing" if trial_days > 0 else "active",
            trial_ends_at=trial_ends_at,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        return subscription

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        subscription_id: int,
        at_period_end: bool = True,
    ) -> Subscription:
        """
        Cancel subscription.

        Args:
            db: Database session
            subscription_id: Subscription ID
            at_period_end: Cancel at period end or immediately

        Returns:
            Updated Subscription
        """
        subscription = await db.get(Subscription, subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")

        # Cancel in Stripe if configured
        if STRIPE_AVAILABLE and subscription.stripe_subscription_id:
            try:
                if at_period_end:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                else:
                    stripe.Subscription.delete(subscription.stripe_subscription_id)
            except Exception as e:
                print(f"Error cancelling Stripe subscription: {e}")

        # Update local subscription
        subscription.cancel_at_period_end = at_period_end
        if not at_period_end:
            subscription.status = "cancelled"

        await db.commit()
        await db.refresh(subscription)

        return subscription

    @staticmethod
    async def record_usage(
        db: AsyncSession,
        clinic_id: int,
        hours: float,
    ):
        """
        Record transcription usage.

        Args:
            db: Database session
            clinic_id: Clinic ID
            hours: Hours of transcription used
        """
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.clinic_id == clinic_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return

        # Get or create usage record for current month
        month = datetime.utcnow().strftime("%Y-%m")
        result = await db.execute(
            select(UsageRecord).where(
                UsageRecord.subscription_id == subscription.id,
                UsageRecord.period_month == month
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            usage = UsageRecord(
                subscription_id=subscription.id,
                clinic_id=clinic_id,
                period_month=month,
                hours_used=0.0,
                encounters_count=0,
            )
            db.add(usage)

        # Update usage
        usage.hours_used += hours
        usage.encounters_count += 1

        # Calculate overage
        plan = await db.get(SubscriptionPlan, subscription.plan_id)
        if usage.hours_used > plan.hours_included:
            usage.overage_hours = usage.hours_used - plan.hours_included
            usage.overage_charge = usage.overage_hours * BillingService.OVERAGE_RATE

        await db.commit()

    @staticmethod
    async def check_usage_limit(
        db: AsyncSession,
        clinic_id: int,
    ) -> Dict:
        """
        Check if clinic is within usage limits.

        Args:
            db: Database session
            clinic_id: Clinic ID

        Returns:
            Dictionary with usage information
        """
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.clinic_id == clinic_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return {
                "allowed": False,
                "reason": "No active subscription",
                "hours_used": 0,
                "hours_limit": 0,
            }

        if subscription.status not in ["active", "trialing"]:
            return {
                "allowed": False,
                "reason": f"Subscription status: {subscription.status}",
                "hours_used": 0,
                "hours_limit": 0,
            }

        # Get plan
        plan = await db.get(SubscriptionPlan, subscription.plan_id)

        # Get current month usage
        month = datetime.utcnow().strftime("%Y-%m")
        result = await db.execute(
            select(UsageRecord).where(
                UsageRecord.subscription_id == subscription.id,
                UsageRecord.period_month == month
            )
        )
        usage = result.scalar_one_or_none()

        hours_used = usage.hours_used if usage else 0.0

        # Allow overage (will be billed)
        return {
            "allowed": True,
            "status": subscription.status,
            "plan_name": plan.name,
            "hours_used": round(hours_used, 2),
            "hours_limit": plan.hours_included,
            "hours_remaining": max(0, plan.hours_included - hours_used),
            "overage_hours": max(0, hours_used - plan.hours_included),
            "overage_charge": max(0, hours_used - plan.hours_included) * BillingService.OVERAGE_RATE,
            "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
        }

    @staticmethod
    async def has_feature(
        db: AsyncSession,
        clinic_id: int,
        feature: str,
    ) -> bool:
        """
        Check if clinic's plan includes a feature.

        Args:
            db: Database session
            clinic_id: Clinic ID
            feature: Feature name

        Returns:
            True if feature is included
        """
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.clinic_id == clinic_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription or subscription.status not in ["active", "trialing"]:
            return False

        # Get plan
        plan = await db.get(SubscriptionPlan, subscription.plan_id)
        if not plan or not plan.features:
            return False

        return feature in plan.features


# Global service instance
billing_service = BillingService()
