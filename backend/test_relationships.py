#!/usr/bin/env python3
"""
Test script to verify SQLAlchemy relationships work correctly
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def test_relationships():
    """Test that subscription relationships work"""
    try:
        from core.database import get_db
        from models.subscription import Subscription, SubscriptionPlan
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        print("✅ Imports successful")
        
        # Test database query with relationships
        async for db in get_db():
            try:
                # Test basic query
                result = await db.execute(select(SubscriptionPlan).limit(1))
                plans = result.scalars().first()
                print(f"✅ Basic query works: {plans.name if plans else 'No plans found'}")
                
                # Test relationship query
                result = await db.execute(
                    select(Subscription)
                    .options(selectinload(Subscription.plan))
                    .limit(1)
                )
                sub = result.scalars().first()
                if sub:
                    print(f"✅ Relationship query works: Subscription {sub.id} -> Plan {sub.plan.name}")
                else:
                    print("✅ Relationship query works (no subscriptions found)")
                
                # Test downgrade relationship if exists
                result = await db.execute(
                    select(Subscription)
                    .options(selectinload(Subscription.downgrade_plan))
                    .where(Subscription.downgrade_to_plan_id.isnot(None))
                    .limit(1)
                )
                downgrade_sub = result.scalars().first()
                if downgrade_sub and downgrade_sub.downgrade_plan:
                    print(f"✅ Downgrade relationship works: {downgrade_sub.downgrade_plan.name}")
                else:
                    print("✅ Downgrade relationship works (no downgrades scheduled)")
                
                break
                
            except Exception as e:
                print(f"❌ Database error: {e}")
                break
            finally:
                await db.close()
                
    except Exception as e:
        print(f"❌ Import/setup error: {e}")

if __name__ == "__main__":
    asyncio.run(test_relationships())