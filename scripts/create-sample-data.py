#!/usr/bin/env python3
"""Create sample data for development and testing."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.clinic import Clinic
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def create_sample_data():
    """Create sample clinics and users."""
    async with AsyncSessionLocal() as db:
        # Check if data already exists
        from sqlalchemy import select
        result = await db.execute(select(Clinic))
        existing = result.scalar_one_or_none()

        if existing:
            print("Sample data already exists. Skipping...")
            return

        # Create sample clinic
        clinic = Clinic(
            name="Sydney General Practice",
            data_residency="AU",
            retention_days=90,
            kms_key_id="default-key",
            active=True,
        )
        db.add(clinic)
        await db.commit()
        await db.refresh(clinic)

        print(f"✅ Created clinic: {clinic.name} (ID: {clinic.id})")

        # Create sample users
        users_data = [
            {
                "email": "doctor@example.com",
                "password": "password123",
                "full_name": "Dr. Sarah Smith",
                "role": UserRole.DOCTOR,
            },
            {
                "email": "nurse@example.com",
                "password": "password123",
                "full_name": "Nurse John Doe",
                "role": UserRole.NURSE,
            },
            {
                "email": "admin@example.com",
                "password": "password123",
                "full_name": "Admin User",
                "role": UserRole.ADMIN,
            },
        ]

        for user_data in users_data:
            user = User(
                clinic_id=clinic.id,
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
                active=True,
            )
            db.add(user)
            print(f"✅ Created user: {user.email} (Role: {user.role.value})")

        await db.commit()

        print("\n🎉 Sample data created successfully!")
        print("\nTest credentials:")
        print("  Doctor: doctor@example.com / password123")
        print("  Nurse: nurse@example.com / password123")
        print("  Admin: admin@example.com / password123")


if __name__ == "__main__":
    asyncio.run(create_sample_data())
