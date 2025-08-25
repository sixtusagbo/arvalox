import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.subscription_service import SubscriptionService
from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    UsageRecord,
    PlanType,
    BillingInterval,
    SubscriptionStatus,
)


class TestSubscriptionService:
    """Test SubscriptionService functionality"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db_mock = AsyncMock()
        # Make synchronous methods use MagicMock to avoid coroutine warnings
        db_mock.add = MagicMock()
        return db_mock

    @pytest.mark.asyncio
    async def test_create_default_plans(self, mock_db):
        """Test creating default subscription plans"""
        # Mock no existing plans
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        plans = await SubscriptionService.create_default_plans(mock_db)
        
        assert len(plans) == 3
        assert plans[0].plan_type == PlanType.FREE
        assert plans[1].plan_type == PlanType.PROFESSIONAL
        assert plans[2].plan_type == PlanType.ENTERPRISE
        
        # Verify pricing is in NGN
        assert plans[1].monthly_price == Decimal("25000.00")
        assert plans[1].yearly_price == Decimal("250000.00")
        assert plans[1].currency == "NGN"
        
        # Verify feature differences
        assert plans[0].api_access is False  # Free plan
        assert plans[1].api_access is True   # Professional plan
        assert plans[1].custom_branding is True   # Professional plan
        assert plans[2].max_invoices_per_month is None  # Enterprise unlimited

    @pytest.mark.asyncio
    async def test_get_all_plans(self, mock_db):
        """Test getting all active plans"""
        mock_plans = [
            SubscriptionPlan(name="Free", plan_type=PlanType.FREE, is_active=True, sort_order=1),
            SubscriptionPlan(name="Professional Plan", plan_type=PlanType.PROFESSIONAL, is_active=True, sort_order=2),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_plans
        mock_db.execute.return_value = mock_result

        plans = await SubscriptionService.get_all_plans(mock_db)
        
        assert len(plans) == 2
        assert plans[0].name == "Free"
        assert plans[1].name == "Professional Plan"

    @pytest.mark.asyncio
    async def test_get_plan_by_type(self, mock_db):
        """Test getting plan by type"""
        mock_plan = SubscriptionPlan(name="Professional Plan", plan_type=PlanType.PROFESSIONAL)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_plan
        mock_db.execute.return_value = mock_result

        plan = await SubscriptionService.get_plan_by_type(mock_db, PlanType.PROFESSIONAL)
        
        assert plan is not None
        assert plan.name == "Professional Plan"
        assert plan.plan_type == PlanType.PROFESSIONAL

    @pytest.mark.asyncio
    async def test_create_subscription_with_trial(self, mock_db):
        """Test creating subscription with trial"""
        subscription = await SubscriptionService.create_subscription(
            db=mock_db,
            organization_id=1,
            plan_id=2,
            billing_interval=BillingInterval.MONTHLY,
            start_trial=True,
            trial_days=14,
        )

        # Verify subscription was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify subscription properties
        assert subscription.organization_id == 1
        assert subscription.plan_id == 2
        assert subscription.status == SubscriptionStatus.TRIALING
        assert subscription.billing_interval == BillingInterval.MONTHLY
        assert subscription.current_team_member_count == 1  # Owner

    @pytest.mark.asyncio
    async def test_create_subscription_without_trial(self, mock_db):
        """Test creating subscription without trial"""
        subscription = await SubscriptionService.create_subscription(
            db=mock_db,
            organization_id=1,
            plan_id=2,
            start_trial=False,
        )

        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.trial_start is None
        assert subscription.trial_end is None

    @pytest.mark.asyncio
    async def test_get_organization_subscription(self, mock_db):
        """Test getting organization subscription"""
        mock_subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        subscription = await SubscriptionService.get_organization_subscription(mock_db, 1)
        
        assert subscription is not None
        assert subscription.organization_id == 1

    @pytest.mark.asyncio
    async def test_upgrade_subscription(self, mock_db):
        """Test upgrading subscription plan"""
        mock_subscription = Subscription(
            id=1,
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.TRIALING,
            billing_interval=BillingInterval.MONTHLY,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        updated_subscription = await SubscriptionService.upgrade_subscription(
            db=mock_db,
            subscription_id=1,
            new_plan_id=2,
            billing_interval=BillingInterval.YEARLY,
        )

        assert updated_subscription.plan_id == 2
        assert updated_subscription.billing_interval == BillingInterval.YEARLY
        assert updated_subscription.status == SubscriptionStatus.ACTIVE  # Upgraded from trial

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediate(self, mock_db):
        """Test immediate subscription cancellation"""
        mock_subscription = Subscription(
            id=1,
            status=SubscriptionStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        canceled_subscription = await SubscriptionService.cancel_subscription(
            db=mock_db,
            subscription_id=1,
            cancel_immediately=True,
        )

        assert canceled_subscription.status == SubscriptionStatus.CANCELED
        assert canceled_subscription.canceled_at is not None
        assert canceled_subscription.ended_at is not None

    @pytest.mark.asyncio
    async def test_cancel_subscription_end_of_period(self, mock_db):
        """Test subscription cancellation at end of period"""
        mock_subscription = Subscription(
            id=1,
            status=SubscriptionStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        canceled_subscription = await SubscriptionService.cancel_subscription(
            db=mock_db,
            subscription_id=1,
            cancel_immediately=False,
        )

        assert canceled_subscription.status == SubscriptionStatus.CANCELED
        assert canceled_subscription.canceled_at is not None
        assert canceled_subscription.ended_at is None  # Runs until period end

    @pytest.mark.asyncio
    async def test_reactivate_subscription(self, mock_db):
        """Test reactivating canceled subscription"""
        past_date = datetime.now(timezone.utc) - timedelta(days=5)
        mock_subscription = Subscription(
            id=1,
            status=SubscriptionStatus.CANCELED,
            billing_interval=BillingInterval.MONTHLY,
            current_period_end=past_date,  # Expired
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        reactivated_subscription = await SubscriptionService.reactivate_subscription(
            db=mock_db,
            subscription_id=1,
        )

        assert reactivated_subscription.status == SubscriptionStatus.ACTIVE
        assert reactivated_subscription.canceled_at is None
        assert reactivated_subscription.ended_at is None
        # Should extend period since it was expired
        assert reactivated_subscription.current_period_end > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_update_usage_count(self, mock_db):
        """Test updating subscription usage counters"""
        mock_subscription = Subscription(
            id=1,
            current_invoice_count=5,
            current_customer_count=10,
            current_team_member_count=2,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        updated_subscription = await SubscriptionService.update_usage_count(
            db=mock_db,
            subscription_id=1,
            invoice_count_delta=3,
            customer_count_delta=2,
            team_member_count_delta=1,
        )

        assert updated_subscription.current_invoice_count == 8
        assert updated_subscription.current_customer_count == 12
        assert updated_subscription.current_team_member_count == 3

    @pytest.mark.asyncio
    async def test_update_usage_count_minimum_limits(self, mock_db):
        """Test usage count updates respect minimum limits"""
        mock_subscription = Subscription(
            id=1,
            current_invoice_count=2,
            current_customer_count=3,
            current_team_member_count=2,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        updated_subscription = await SubscriptionService.update_usage_count(
            db=mock_db,
            subscription_id=1,
            invoice_count_delta=-5,  # Would go negative
            customer_count_delta=-5,  # Would go negative
            team_member_count_delta=-3,  # Would go below 1
        )

        assert updated_subscription.current_invoice_count == 0  # Min 0
        assert updated_subscription.current_customer_count == 0  # Min 0
        assert updated_subscription.current_team_member_count == 1  # Min 1 for owner

    @pytest.mark.asyncio
    async def test_create_or_update_usage_record_new(self, mock_db):
        """Test creating new usage record"""
        # Mock no existing record
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        usage_record = await SubscriptionService.create_or_update_usage_record(
            db=mock_db,
            subscription_id=1,
            month=8,
            year=2023,
            invoices_created=10,
            customers_created=5,
        )

        # Verify new record was added
        mock_db.add.assert_called_once()
        assert usage_record.invoices_created == 10
        assert usage_record.customers_created == 5

    @pytest.mark.asyncio
    async def test_create_or_update_usage_record_existing(self, mock_db):
        """Test updating existing usage record"""
        existing_record = UsageRecord(
            subscription_id=1,
            month=8,
            year=2023,
            invoices_created=5,
            customers_created=3,
            team_members_added=0,
            api_calls_made=0,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_record
        mock_db.execute.return_value = mock_result

        usage_record = await SubscriptionService.create_or_update_usage_record(
            db=mock_db,
            subscription_id=1,
            month=8,
            year=2023,
            invoices_created=7,
            customers_created=2,
        )

        # Should have updated existing record
        mock_db.add.assert_not_called()
        assert usage_record.invoices_created == 12  # 5 + 7
        assert usage_record.customers_created == 5   # 3 + 2

    @pytest.mark.asyncio
    async def test_get_expiring_subscriptions(self, mock_db):
        """Test getting subscriptions expiring soon"""
        mock_subscriptions = [
            Subscription(id=1, current_period_end=datetime.now(timezone.utc) + timedelta(days=3)),
            Subscription(id=2, current_period_end=datetime.now(timezone.utc) + timedelta(days=5)),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_subscriptions
        mock_db.execute.return_value = mock_result

        expiring_subscriptions = await SubscriptionService.get_expiring_subscriptions(
            db=mock_db,
            days_ahead=7,
        )

        assert len(expiring_subscriptions) == 2

    @pytest.mark.asyncio
    async def test_reset_monthly_usage_counts(self, mock_db):
        """Test resetting monthly usage counts"""
        mock_subscriptions = [
            Subscription(id=1, current_invoice_count=50, status=SubscriptionStatus.ACTIVE),
            Subscription(id=2, current_invoice_count=25, status=SubscriptionStatus.TRIALING),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_subscriptions
        mock_db.execute.return_value = mock_result

        await SubscriptionService.reset_monthly_usage_counts(mock_db)

        # Verify invoice counts were reset
        assert mock_subscriptions[0].current_invoice_count == 0
        assert mock_subscriptions[1].current_invoice_count == 0
        
        mock_db.commit.assert_called_once()