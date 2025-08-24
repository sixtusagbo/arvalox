from datetime import datetime, timedelta, timezone
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
from app.services.paystack_service import PaystackService


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
        now = datetime.now(timezone.utc)
        
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
            now = datetime.now(timezone.utc)
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
        
        now = datetime.now(timezone.utc)
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
        now = datetime.now(timezone.utc)
        # Make sure we're comparing timezone-aware datetimes
        current_end = subscription.current_period_end
        if current_end.tzinfo is None:
            current_end = current_end.replace(tzinfo=timezone.utc)
        if current_end <= now:
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
        auto_commit: bool = True,
    ) -> Subscription:
        """Update usage counters for a subscription with monthly reset support"""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        # Use the new reset-aware methods
        if invoice_count_delta > 0:
            for _ in range(invoice_count_delta):
                subscription.increment_invoice_count()
        elif invoice_count_delta < 0:
            subscription.reset_monthly_usage_if_needed()
            subscription.current_invoice_count = max(0, subscription.current_invoice_count + invoice_count_delta)
        
        if customer_count_delta != 0:
            if customer_count_delta > 0:
                for _ in range(customer_count_delta):
                    subscription.increment_customer_count()
            else:
                subscription.current_customer_count = max(0, subscription.current_customer_count + customer_count_delta)
        
        if team_member_count_delta != 0:
            if team_member_count_delta > 0:
                for _ in range(team_member_count_delta):
                    subscription.increment_team_member_count()
            else:
                subscription.current_team_member_count = max(1, subscription.current_team_member_count + team_member_count_delta)  # Min 1 for owner
        
        if auto_commit:
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
        future_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
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

    @staticmethod
    async def sync_usage_counts_from_database(
        db: AsyncSession,
        subscription_id: int
    ) -> Subscription:
        """Sync usage counts with actual database counts"""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.organization))
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        # Get actual counts from database
        from app.models.invoice import Invoice
        from app.models.customer import Customer
        from app.models.user import User
        
        # Count invoices for this organization
        invoice_result = await db.execute(
            select(Invoice)
            .where(Invoice.organization_id == subscription.organization_id)
        )
        invoice_count = len(invoice_result.scalars().all())
        
        # Count customers for this organization
        customer_result = await db.execute(
            select(Customer)
            .where(Customer.organization_id == subscription.organization_id)
        )
        customer_count = len(customer_result.scalars().all())
        
        # Count team members for this organization
        user_result = await db.execute(
            select(User)
            .where(User.organization_id == subscription.organization_id)
        )
        team_member_count = len(user_result.scalars().all())
        
        # Update subscription counts
        subscription.current_invoice_count = invoice_count
        subscription.current_customer_count = customer_count
        subscription.current_team_member_count = max(1, team_member_count)  # Min 1 for owner
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def initialize_paystack_payment(
        db: AsyncSession,
        organization_id: int,
        plan_id: int,
        billing_interval: BillingInterval,
        user_email: str,
        user_first_name: str,
        user_last_name: str,
        organization_name: str,
        callback_url: str
    ) -> dict:
        """Initialize Paystack payment for subscription"""
        paystack = PaystackService()
        
        # Get plan details
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = result.scalar_one()
        
        # Determine amount based on billing interval
        amount = plan.monthly_price if billing_interval == BillingInterval.MONTHLY else plan.yearly_price
        
        # Initialize transaction
        transaction_data = await paystack.initialize_transaction(
            email=user_email,
            amount=amount,
            plan_id=plan_id,
            organization_name=organization_name,
            billing_interval=billing_interval,
            callback_url=callback_url,
            metadata={
                "organization_id": organization_id,
                "user_first_name": user_first_name,
                "user_last_name": user_last_name
            }
        )
        
        return transaction_data

    @staticmethod
    async def process_successful_payment(
        db: AsyncSession,
        transaction_reference: str,
        organization_id: int,
        plan_id: int,
        billing_interval: BillingInterval
    ) -> Subscription:
        """Process successful payment and create/update subscription"""
        paystack = PaystackService()
        
        # Verify transaction
        transaction_data = await paystack.verify_transaction(transaction_reference)
        
        if transaction_data["status"] != "success":
            raise Exception("Transaction was not successful")
            
        # Get plan details
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = result.scalar_one()
        
        # Check if subscription already exists
        existing_result = await db.execute(
            select(Subscription).where(Subscription.organization_id == organization_id)
        )
        existing_subscription = existing_result.scalar_one_or_none()
        
        if existing_subscription:
            # Update existing subscription
            existing_subscription.plan_id = plan_id
            existing_subscription.billing_interval = billing_interval
            existing_subscription.status = SubscriptionStatus.ACTIVE
            existing_subscription.paystack_customer_code = transaction_data.get("customer", {}).get("customer_code")
            
            # Reset trial if it was trial
            if existing_subscription.status == SubscriptionStatus.TRIALING:
                existing_subscription.trial_end = None
                existing_subscription.trial_start = None
            
            await db.commit()
            await db.refresh(existing_subscription)
            return existing_subscription
        else:
            # Create new subscription
            subscription = await SubscriptionService.create_subscription(
                db=db,
                organization_id=organization_id,
                plan_id=plan_id,
                billing_interval=billing_interval,
                start_trial=False  # Since they paid, no trial needed
            )
            
            # Add Paystack customer info
            subscription.paystack_customer_code = transaction_data.get("customer", {}).get("customer_code")
            
            await db.commit()
            await db.refresh(subscription)
            return subscription

    @staticmethod
    async def setup_paystack_plans(db: AsyncSession) -> None:
        """Create Paystack plans for all subscription plans"""
        paystack = PaystackService()
        
        # Get all active plans
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
        )
        plans = result.scalars().all()
        
        for plan in plans:
            # Skip free plan
            if plan.plan_type == PlanType.FREE:
                continue
                
            # Create monthly plan if not exists
            if not plan.paystack_plan_code_monthly and plan.monthly_price > 0:
                monthly_plan = await paystack.create_subscription_plan(plan, BillingInterval.MONTHLY)
                plan.paystack_plan_code_monthly = monthly_plan["plan_code"]
            
            # Create yearly plan if not exists
            if not plan.paystack_plan_code_yearly and plan.yearly_price > 0:
                yearly_plan = await paystack.create_subscription_plan(plan, BillingInterval.YEARLY)
                plan.paystack_plan_code_yearly = yearly_plan["plan_code"]
        
        await db.commit()

    @staticmethod
    async def verify_paystack_payment(
        db: AsyncSession,
        transaction_reference: str,
        plan_id: int,
        billing_interval: BillingInterval,
        organization_id: int
    ) -> Subscription:
        """Verify Paystack payment and create/update subscription"""
        return await SubscriptionService.process_successful_payment(
            db=db,
            transaction_reference=transaction_reference,
            organization_id=organization_id,
            plan_id=plan_id,
            billing_interval=billing_interval
        )

    @staticmethod
    async def schedule_downgrade(
        db: AsyncSession,
        subscription_id: int,
        target_plan_id: int
    ) -> Subscription:
        """Schedule a downgrade to take effect at end of current billing period"""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan), selectinload(Subscription.downgrade_plan))
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        # Validate target plan exists
        target_plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == target_plan_id)
        )
        target_plan = target_plan_result.scalar_one_or_none()
        if not target_plan:
            raise ValueError(f"Target plan with ID {target_plan_id} not found")
        
        # Schedule the downgrade
        subscription.schedule_downgrade(target_plan_id)
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def cancel_scheduled_downgrade(
        db: AsyncSession,
        subscription_id: int
    ) -> Subscription:
        """Cancel a scheduled downgrade"""
        result = await db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        subscription.cancel_downgrade()
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def process_scheduled_downgrades(db: AsyncSession) -> List[Subscription]:
        """Process all scheduled downgrades that are due"""
        now = datetime.now(timezone.utc)
        
        # Find subscriptions with downgrades due
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan), selectinload(Subscription.downgrade_plan))
            .where(
                and_(
                    Subscription.downgrade_to_plan_id.isnot(None),
                    Subscription.downgrade_effective_date <= now
                )
            )
        )
        subscriptions = result.scalars().all()
        
        processed = []
        for subscription in subscriptions:
            if subscription.apply_downgrade():
                processed.append(subscription)
        
        if processed:
            await db.commit()
            for sub in processed:
                await db.refresh(sub)
        
        return processed

    @staticmethod
    async def update_subscription_with_usage_reset(
        db: AsyncSession,
        subscription_id: int,
        plan_id: int,
        billing_interval: BillingInterval | None = None
    ) -> Subscription:
        """Update subscription plan with enhanced downgrade logic"""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one()
        
        # Get target plan
        target_plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        target_plan = target_plan_result.scalar_one()
        
        # Determine if this is a downgrade (higher tier to lower tier)
        current_plan_tiers = {
            PlanType.FREE: 0,
            PlanType.STARTER: 1,
            PlanType.PROFESSIONAL: 2,
            PlanType.ENTERPRISE: 3
        }
        
        current_tier = current_plan_tiers.get(subscription.plan.plan_type, 0)
        target_tier = current_plan_tiers.get(target_plan.plan_type, 0)
        
        # If downgrading and subscription is paid (not free), schedule the downgrade
        if (target_tier < current_tier and 
            subscription.plan.plan_type != PlanType.FREE and 
            subscription.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]):
            
            return await SubscriptionService.schedule_downgrade(db, subscription_id, plan_id)
        else:
            # Immediate upgrade or free plan switch
            subscription.plan_id = plan_id
            
            # Update billing interval if provided
            if billing_interval:
                subscription.billing_interval = billing_interval
                
                # Recalculate period for free plans or upgrades
                now = datetime.now(timezone.utc)
                if billing_interval == BillingInterval.YEARLY:
                    subscription.current_period_end = now + timedelta(days=365)
                else:
                    subscription.current_period_end = now + timedelta(days=30)
                subscription.current_period_start = now
            
            # Reset usage for monthly counter when changing plans
            subscription.reset_monthly_usage_if_needed()
            
            # If upgrading from trial, make it active
            if subscription.status == SubscriptionStatus.TRIALING:
                subscription.status = SubscriptionStatus.ACTIVE
            
            await db.commit()
            await db.refresh(subscription)
            
            return subscription