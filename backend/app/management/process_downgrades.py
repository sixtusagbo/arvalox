#!/usr/bin/env python3
"""
Background job to process scheduled subscription downgrades.
Should be run as a cron job (e.g., daily at midnight).
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_db
from services.subscription_service import SubscriptionService


async def process_downgrades():
    """Process all scheduled downgrades that are due"""
    print(f"[{datetime.now(timezone.utc)}] Starting downgrade processing...")
    
    async for db in get_db():
        try:
            processed_subscriptions = await SubscriptionService.process_scheduled_downgrades(db)
            
            if processed_subscriptions:
                print(f"Processed {len(processed_subscriptions)} downgrades:")
                for sub in processed_subscriptions:
                    print(f"  - Subscription {sub.id} (Org {sub.organization_id}) -> Plan {sub.plan_id}")
            else:
                print("No downgrades were due for processing.")
                
        except Exception as e:
            print(f"Error processing downgrades: {str(e)}")
            raise
        finally:
            await db.close()
    
    print(f"[{datetime.now(timezone.utc)}] Downgrade processing completed.")


async def reset_monthly_usage():
    """Reset monthly usage counters for all subscriptions (run monthly)"""
    print(f"[{datetime.now(timezone.utc)}] Starting monthly usage reset...")
    
    async for db in get_db():
        try:
            # This will be handled automatically by the subscription models
            # when they check if a new billing period has started
            print("Monthly usage reset is handled automatically on invoice creation.")
                
        except Exception as e:
            print(f"Error during monthly reset: {str(e)}")
            raise
        finally:
            await db.close()
    
    print(f"[{datetime.now(timezone.utc)}] Monthly usage reset completed.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process subscription downgrades')
    parser.add_argument('--type', choices=['downgrades', 'reset'], default='downgrades',
                        help='Type of processing to run')
    
    args = parser.parse_args()
    
    if args.type == 'downgrades':
        asyncio.run(process_downgrades())
    elif args.type == 'reset':
        asyncio.run(reset_monthly_usage())