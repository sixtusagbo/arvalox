from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    UsageRecord,
    PlanType,
    BillingInterval,
    SubscriptionStatus,
)
from app.models.organization import Organization


class SubscriptionService:
    """Service for managing subscriptions and plans"""

    @staticmethod
    async def create_default_plans(db: AsyncSession) -> List[SubscriptionPlan]:
        """Create default subscription plans with NGN pricing"""
        plans = [
            SubscriptionPlan(
                name="Free Plan",
                plan_type=PlanType.FREE,
                description="Perfect for trying out Arvalox",
                monthly_price=Decimal("0.00"),
                yearly_price=Decimal("0.00"),
                currency="NGN",
                max_invoices_per_month=5,
                max_customers=10,
                max_team_members=1,
                custom_branding=False,
                api_access=False,
                advanced_reporting=False,
                priority_support=False,
                multi_currency=False,
                is_active=True,
                sort_order=1,
            ),
            SubscriptionPlan(
                name="Starter Plan",
                plan_type=PlanType.STARTER,
                description="Great for small businesses getting started",
                monthly_price=Decimal("15000.00"),  # ₦15,000/month
                yearly_price=Decimal("150000.00"),  # ₦150,000/year (2 months free)
                currency="NGN",
                max_invoices_per_month=100,
                max_customers=500,
                max_team_members=5,
                custom_branding=False,
                api_access=True,
                advanced_reporting=True,
                priority_support=False,
                multi_currency=True,
                is_active=True,
                sort_order=2,
            ),
            SubscriptionPlan(
                name="Professional Plan",
                plan_type=PlanType.PROFESSIONAL,
                description="Perfect for growing businesses",
                monthly_price=Decimal("35000.00"),  # ₦35,000/month
                yearly_price=Decimal("350000.00"),  # ₦350,000/year (2 months free)
                currency="NGN",
                max_invoices_per_month=1000,
                max_customers=2000,
                max_team_members=15,
                custom_branding=True,
                api_access=True,
                advanced_reporting=True,
                priority_support=True,
                multi_currency=True,
                is_active=True,
                sort_order=3,
            ),
            SubscriptionPlan(
                name="Enterprise Plan",
                plan_type=PlanType.ENTERPRISE,
                description="Unlimited power for large organizations",
                monthly_price=Decimal("75000.00"),  # ₦75,000/month
                yearly_price=Decimal("750000.00"),  # ₦750,000/year (2 months free)
                currency="NGN",
                max_invoices_per_month=None,  # Unlimited
                max_customers=None,  # Unlimited
                max_team_members=None,  # Unlimited
                custom_branding=True,
                api_access=True,
                advanced_reporting=True,
                priority_support=True,
                multi_currency=True,
                is_active=True,
                sort_order=4,
            ),
        ]

        # Check if plans already exist
        result = await db.execute(select(SubscriptionPlan))
        existing_plans = result.scalars().all()
        
        if not existing_plans:
            for plan in plans:
                db.add(plan)
            await db.commit()
            
            # Refresh to get IDs
            for plan in plans:
                await db.refresh(plan)
        
        return plans

    @staticmethod
    async def get_all_plans(db: AsyncSession) -> List[SubscriptionPlan]:
        """Get all active subscription plans"""
        result = await db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active == True)
            .order_by(SubscriptionPlan.sort_order)
        )
        return result.scalars().all()

    @staticmethod
    async def get_plan_by_type(db: AsyncSession, plan_type: PlanType) -> Optional[SubscriptionPlan]:
        """Get a plan by its type"""
        result = await db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.plan_type == plan_type)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        organization_id: int,
        plan_id: int,
        billing_interval: BillingInterval = BillingInterval.MONTHLY,
        start_trial: bool = True,
        trial_days: int = 14,
    ) -> Subscription:
        """Create a new subscription for an organization"""
        now = datetime.utcnow()
        
        # Calculate period dates
        if billing_interval == BillingInterval.YEARLY:
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)
        
        subscription_data = {
            "organization_id": organization_id,
            "plan_id": plan_id,
            "status": SubscriptionStatus.TRIALING if start_trial else SubscriptionStatus.ACTIVE,
            "billing_interval": billing_interval,
            "started_at": now,
            "current_period_start": now,
            "current_period_end": period_end,
            "current_invoice_count": 0,
            "current_customer_count": 0,
            "current_team_member_count": 1,  # Owner counts as 1
        }
        
        # Add trial dates if starting trial
        if start_trial:
            subscription_data["trial_start"] = now
            subscription_data["trial_end"] = now + timedelta(days=trial_days)
        
        subscription = Subscription(**subscription_data)
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def get_organization_subscription(
        db: AsyncSession, 
        organization_id: int
    ) -> Optional[Subscription]:
        """Get an organization's current subscription"""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upgrade_subscription(
        db: AsyncSession,
        subscription_id: int,
        new_plan_id: int,
        billing_interval: Optional[BillingInterval] = None,
    ) -> Subscription:
        """Upgrade/change a subscription plan"""
        # Get current subscription
        result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        # Update plan
        subscription.plan_id = new_plan_id
        
        # Update billing interval if provided
        if billing_interval:
            subscription.billing_interval = billing_interval
            
            # Recalculate period end based on new billing interval
            now = datetime.utcnow()
            if billing_interval == BillingInterval.YEARLY:
                subscription.current_period_end = now + timedelta(days=365)
            else:
                subscription.current_period_end = now + timedelta(days=30)
        
        # If upgrading from trial, make it active
        if subscription.status == SubscriptionStatus.TRIALING:
            subscription.status = SubscriptionStatus.ACTIVE
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        subscription_id: int,
        cancel_immediately: bool = False,
    ) -> Subscription:
        """Cancel a subscription"""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        now = datetime.utcnow()
        subscription.canceled_at = now
        
        if cancel_immediately:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.ended_at = now
        else:
            # Let it run until end of current period
            subscription.status = SubscriptionStatus.CANCELED
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def reactivate_subscription(
        db: AsyncSession,
        subscription_id: int,
    ) -> Subscription:
        """Reactivate a canceled subscription"""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.canceled_at = None
        subscription.ended_at = None
        
        # Extend current period if it has passed
        now = datetime.utcnow()
        if subscription.current_period_end <= now:
            if subscription.billing_interval == BillingInterval.YEARLY:
                subscription.current_period_end = now + timedelta(days=365)
            else:
                subscription.current_period_end = now + timedelta(days=30)
            subscription.current_period_start = now
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def update_usage_count(
        db: AsyncSession,
        subscription_id: int,
        invoice_count_delta: int = 0,
        customer_count_delta: int = 0,
        team_member_count_delta: int = 0,
    ) -> Subscription:
        """Update usage counters for a subscription"""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        # Update counters
        subscription.current_invoice_count += invoice_count_delta
        subscription.current_customer_count += customer_count_delta
        subscription.current_team_member_count += team_member_count_delta
        
        # Ensure counters don't go below 0
        subscription.current_invoice_count = max(0, subscription.current_invoice_count)
        subscription.current_customer_count = max(0, subscription.current_customer_count)
        subscription.current_team_member_count = max(1, subscription.current_team_member_count)  # Min 1 for owner
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def get_usage_record(
        db: AsyncSession,
        subscription_id: int,
        month: int,
        year: int,
    ) -> Optional[UsageRecord]:
        """Get usage record for a specific month"""
        result = await db.execute(
            select(UsageRecord)
            .where(
                and_(
                    UsageRecord.subscription_id == subscription_id,
                    UsageRecord.month == month,
                    UsageRecord.year == year,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_update_usage_record(
        db: AsyncSession,
        subscription_id: int,
        month: int,
        year: int,
        invoices_created: int = 0,
        customers_created: int = 0,
        team_members_added: int = 0,
        api_calls_made: int = 0,
    ) -> UsageRecord:
        """Create or update a usage record"""
        # Try to get existing record
        usage_record = await SubscriptionService.get_usage_record(
            db, subscription_id, month, year
        )
        
        if usage_record:
            # Update existing record
            usage_record.invoices_created += invoices_created
            usage_record.customers_created += customers_created
            usage_record.team_members_added += team_members_added
            usage_record.api_calls_made += api_calls_made
        else:
            # Create new record
            usage_record = UsageRecord(
                subscription_id=subscription_id,
                month=month,
                year=year,
                invoices_created=invoices_created,
                customers_created=customers_created,
                team_members_added=team_members_added,
                api_calls_made=api_calls_made,
            )
            db.add(usage_record)
        
        await db.commit()
        await db.refresh(usage_record)
        
        return usage_record

    @staticmethod
    async def get_expiring_subscriptions(
        db: AsyncSession,
        days_ahead: int = 7,
    ) -> List[Subscription]:
        """Get subscriptions expiring within specified days"""
        future_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.organization), selectinload(Subscription.plan))
            .where(
                and_(
                    Subscription.current_period_end <= future_date,
                    Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
                )
            )
        )
        return result.scalars().all()

    @staticmethod
    async def reset_monthly_usage_counts(db: AsyncSession) -> None:
        """Reset monthly usage counters for all active subscriptions"""
        result = await db.execute(
            select(Subscription)
            .where(
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIALING
                ])
            )
        )
        subscriptions = result.scalars().all()
        
        for subscription in subscriptions:
            subscription.current_invoice_count = 0
            # Note: We don't reset customer and team member counts as they're cumulative
        
        await db.commit()