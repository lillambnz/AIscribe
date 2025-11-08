"""Billing and subscription API endpoints."""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.subscription import Subscription, SubscriptionPlan, UsageRecord
from app.models.clinic import Clinic
from app.services.billing_service import billing_service

router = APIRouter()


class PlanResponse(BaseModel):
    """Subscription plan response."""
    id: int
    name: str
    display_name: str
    description: str
    price_monthly: float
    price_annual: float
    hours_included: int
    max_users: int
    features: List[str]
    active: bool

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription response."""
    id: int
    clinic_id: int
    plan: PlanResponse
    status: str
    trial_ends_at: str = None
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool

    class Config:
        from_attributes = True


class SubscribeRequest(BaseModel):
    """Subscribe request."""
    plan_id: int
    trial_days: int = 14


class UsageResponse(BaseModel):
    """Usage statistics response."""
    allowed: bool
    status: str
    plan_name: str
    hours_used: float
    hours_limit: int
    hours_remaining: float
    overage_hours: float
    overage_charge: float
    trial_ends_at: str = None


@router.get("/plans", response_model=List[PlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
):
    """Get all available subscription plans."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.active == True)
    )
    plans = result.scalars().all()

    return [
        PlanResponse(
            id=plan.id,
            name=plan.name,
            display_name=plan.display_name,
            description=plan.description or "",
            price_monthly=plan.price_monthly,
            price_annual=plan.price_annual or plan.price_monthly * 10,  # 2 months free
            hours_included=plan.hours_included,
            max_users=plan.max_users or 999,
            features=plan.features or [],
            active=plan.active,
        )
        for plan in plans
    ]


@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    subscribe_req: SubscribeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Subscribe clinic to a plan.

    Creates a new subscription with a trial period.
    """
    clinic_id = int(current_user.get("clinic_id"))

    # Check if already subscribed
    result = await db.execute(
        select(Subscription).where(Subscription.clinic_id == clinic_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinic already has an active subscription",
        )

    # Get clinic for Stripe customer creation
    clinic = await db.get(Clinic, clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    # Create Stripe customer
    stripe_customer_id = await billing_service.create_customer(
        clinic=clinic,
        email=current_user.get("email"),
    )

    # Create subscription
    subscription = await billing_service.create_subscription(
        db=db,
        clinic_id=clinic_id,
        plan_id=subscribe_req.plan_id,
        stripe_customer_id=stripe_customer_id,
        trial_days=subscribe_req.trial_days,
    )

    # Get plan for response
    plan = await db.get(SubscriptionPlan, subscription.plan_id)

    return SubscriptionResponse(
        id=subscription.id,
        clinic_id=subscription.clinic_id,
        plan=PlanResponse(
            id=plan.id,
            name=plan.name,
            display_name=plan.display_name,
            description=plan.description or "",
            price_monthly=plan.price_monthly,
            price_annual=plan.price_annual or plan.price_monthly * 10,
            hours_included=plan.hours_included,
            max_users=plan.max_users or 999,
            features=plan.features or [],
            active=plan.active,
        ),
        status=subscription.status,
        trial_ends_at=subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
        current_period_start=subscription.current_period_start.isoformat(),
        current_period_end=subscription.current_period_end.isoformat(),
        cancel_at_period_end=subscription.cancel_at_period_end,
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription details."""
    clinic_id = int(current_user.get("clinic_id"))

    result = await db.execute(
        select(Subscription).where(Subscription.clinic_id == clinic_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription",
        )

    plan = await db.get(SubscriptionPlan, subscription.plan_id)

    return SubscriptionResponse(
        id=subscription.id,
        clinic_id=subscription.clinic_id,
        plan=PlanResponse(
            id=plan.id,
            name=plan.name,
            display_name=plan.display_name,
            description=plan.description or "",
            price_monthly=plan.price_monthly,
            price_annual=plan.price_annual or plan.price_monthly * 10,
            hours_included=plan.hours_included,
            max_users=plan.max_users or 999,
            features=plan.features or [],
            active=plan.active,
        ),
        status=subscription.status,
        trial_ends_at=subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
        current_period_start=subscription.current_period_start.isoformat(),
        current_period_end=subscription.current_period_end.isoformat(),
        cancel_at_period_end=subscription.cancel_at_period_end,
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current billing period usage."""
    clinic_id = int(current_user.get("clinic_id"))

    usage_info = await billing_service.check_usage_limit(db, clinic_id)

    return UsageResponse(**usage_info)


@router.post("/cancel")
async def cancel_subscription(
    at_period_end: bool = True,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel subscription.

    Args:
        at_period_end: If True, cancel at end of billing period. If False, cancel immediately.
    """
    clinic_id = int(current_user.get("clinic_id"))

    # Get subscription
    result = await db.execute(
        select(Subscription).where(Subscription.clinic_id == clinic_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription",
        )

    # Cancel subscription
    await billing_service.cancel_subscription(
        db=db,
        subscription_id=subscription.id,
        at_period_end=at_period_end,
    )

    return {
        "status": "cancelled" if not at_period_end else "will_cancel",
        "cancel_at": subscription.current_period_end.isoformat() if at_period_end else datetime.utcnow().isoformat(),
    }


@router.get("/usage/history")
async def get_usage_history(
    months: int = 6,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage history for past months."""
    clinic_id = int(current_user.get("clinic_id"))

    # Get subscription
    result = await db.execute(
        select(Subscription).where(Subscription.clinic_id == clinic_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        return {"history": []}

    # Get usage records
    result = await db.execute(
        select(UsageRecord)
        .where(UsageRecord.subscription_id == subscription.id)
        .order_by(UsageRecord.period_month.desc())
        .limit(months)
    )
    records = result.scalars().all()

    return {
        "history": [
            {
                "month": record.period_month,
                "hours_used": record.hours_used,
                "encounters_count": record.encounters_count,
                "overage_hours": record.overage_hours,
                "overage_charge": record.overage_charge,
            }
            for record in records
        ]
    }
