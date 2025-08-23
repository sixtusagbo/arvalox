"""
Data seeding utilities for Arvalox
Run this to populate the database with default subscription plans
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.append(str(backend_dir))

# Set PYTHONPATH environment variable
os.environ["PYTHONPATH"] = str(backend_dir)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionPlan, PlanType


async def seed_subscription_plans():
    """Seed the database with default subscription plans"""
    print("🌱 Seeding subscription plans...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Create default plans
            plans = await SubscriptionService.create_default_plans(db)
            
            if plans:
                print(f"✅ Successfully created {len(plans)} subscription plans:")
                for plan in plans:
                    price_display = f"₦{plan.monthly_price:,.0f}/month" if plan.monthly_price > 0 else "Free"
                    print(f"   - {plan.name} ({plan.plan_type.value}): {price_display}")
            else:
                print("ℹ️  Subscription plans already exist, skipping creation")
                
        except Exception as e:
            print(f"❌ Error seeding subscription plans: {e}")
            raise


async def seed_all():
    """Seed all required data"""
    print("🚀 Starting data seeding process...")
    
    try:
        await seed_subscription_plans()
        print("✅ All data seeded successfully!")
        
    except Exception as e:
        print(f"❌ Data seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_all())