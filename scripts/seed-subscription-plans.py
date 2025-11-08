#!/usr/bin/env python3
"""Seed initial subscription plans."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.subscription import SubscriptionPlan


async def seed_plans():
    """Create initial subscription plans."""
    async with AsyncSessionLocal() as db:
        # Check if plans already exist
        from sqlalchemy import select
        result = await db.execute(select(SubscriptionPlan))
        existing = result.scalar_one_or_none()

        if existing:
            print("Subscription plans already exist. Skipping...")
            return

        plans = [
            {
                "name": "solo",
                "display_name": "Solo Practitioner",
                "description": "Perfect for individual doctors starting out",
                "price_monthly": 149.0,
                "price_annual": 1490.0,  # ~2 months free
                "hours_included": 100,
                "max_users": 1,
                "max_storage_gb": 10,
                "features": [
                    "real_time_transcription",
                    "basic_soap_notes",
                    "pdf_export",
                    "email_support",
                ],
                "active": True,
            },
            {
                "name": "small",
                "display_name": "Small Clinic",
                "description": "For small practices with multiple doctors",
                "price_monthly": 599.0,
                "price_annual": 5990.0,
                "hours_included": 500,
                "max_users": 5,
                "max_storage_gb": 50,
                "features": [
                    "real_time_transcription",
                    "advanced_soap_notes",
                    "medical_entity_extraction",
                    "pdf_export",
                    "custom_templates",
                    "email_support",
                    "usage_analytics",
                ],
                "active": True,
            },
            {
                "name": "medium",
                "display_name": "Medium Practice",
                "description": "For growing practices with advanced needs",
                "price_monthly": 1499.0,
                "price_annual": 14990.0,
                "hours_included": 2000,
                "max_users": 15,
                "max_storage_gb": 200,
                "features": [
                    "real_time_transcription",
                    "advanced_soap_notes",
                    "medical_entity_extraction",
                    "speaker_diarization",
                    "pdf_export",
                    "custom_templates",
                    "api_access",
                    "priority_support",
                    "usage_analytics",
                    "sso_integration",
                ],
                "active": True,
            },
            {
                "name": "enterprise",
                "display_name": "Enterprise",
                "description": "For large practices and hospitals",
                "price_monthly": 3999.0,
                "price_annual": 39990.0,
                "hours_included": 10000,
                "max_users": None,  # Unlimited
                "max_storage_gb": None,  # Unlimited
                "features": [
                    "real_time_transcription",
                    "advanced_soap_notes",
                    "medical_entity_extraction",
                    "speaker_diarization",
                    "pdf_export",
                    "custom_templates",
                    "api_access",
                    "pms_integration",
                    "dedicated_support",
                    "usage_analytics",
                    "sso_integration",
                    "custom_integrations",
                    "on_premise_option",
                    "white_label",
                ],
                "active": True,
            },
        ]

        for plan_data in plans:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            print(f"✅ Created plan: {plan.display_name} - ${plan.price_monthly}/month")

        await db.commit()

        print("\n🎉 Subscription plans created successfully!")
        print("\nAvailable plans:")
        print("  1. Solo Practitioner - $149/month (100 hours)")
        print("  2. Small Clinic - $599/month (500 hours)")
        print("  3. Medium Practice - $1,499/month (2,000 hours)")
        print("  4. Enterprise - $3,999/month (10,000 hours)")


if __name__ == "__main__":
    asyncio.run(seed_plans())
