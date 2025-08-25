import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    UsageRecord,
    PlanType,
    BillingInterval,
    SubscriptionStatus,
)


class TestSubscriptionModels:
    """Test subscription model functionality"""

    def test_subscription_plan_creation(self):
        """Test SubscriptionPlan model creation"""
        plan = SubscriptionPlan(
            name="Professional Plan",
            plan_type=PlanType.PROFESSIONAL,
            description="Perfect for growing businesses",
            monthly_price=Decimal("25000.00"),
            yearly_price=Decimal("250000.00"),
            currency="NGN",
            max_invoices_per_month=500,
            max_customers=1000,
            max_team_members=10,
            custom_branding=True,
            api_access=True,
            advanced_reporting=True,
            priority_support=True,
            multi_currency=True,
        )
        
        assert plan.name == "Professional Plan"
        assert plan.plan_type == PlanType.PROFESSIONAL
        assert plan.monthly_price == Decimal("25000.00")
        assert plan.yearly_price == Decimal("250000.00")
        assert plan.currency == "NGN"
        assert plan.max_invoices_per_month == 500
        assert plan.max_customers == 1000
        assert plan.max_team_members == 10
        assert plan.api_access is True
        assert plan.custom_branding is True

    def test_subscription_creation(self):
        """Test Subscription model creation"""
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=30)
        
        subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=end_date,
            current_invoice_count=5,
            current_customer_count=25,
            current_team_member_count=2,
        )
        
        assert subscription.organization_id == 1
        assert subscription.plan_id == 1
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.billing_interval == BillingInterval.MONTHLY
        assert subscription.current_invoice_count == 5
        assert subscription.current_customer_count == 25
        assert subscription.current_team_member_count == 2

    def test_subscription_is_active_property(self):
        """Test subscription is_active property"""
        now = datetime.now(timezone.utc)
        past_date = now - timedelta(days=1)
        future_date = now + timedelta(days=30)
        
        # Active subscription within period
        active_subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=past_date,
            current_period_start=past_date,
            current_period_end=future_date,
        )
        assert active_subscription.is_active is True
        
        # Expired subscription
        expired_subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=past_date,
            current_period_start=past_date,
            current_period_end=past_date,
        )
        assert expired_subscription.is_active is False
        
        # Canceled subscription
        canceled_subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.CANCELED,
            billing_interval=BillingInterval.MONTHLY,
            started_at=past_date,
            current_period_start=past_date,
            current_period_end=future_date,
        )
        assert canceled_subscription.is_active is False

    def test_subscription_is_trialing_property(self):
        """Test subscription is_trialing property"""
        now = datetime.now(timezone.utc)
        past_date = now - timedelta(days=1)
        future_date = now + timedelta(days=7)
        
        # Active trial
        trial_subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.TRIALING,
            billing_interval=BillingInterval.MONTHLY,
            started_at=past_date,
            current_period_start=past_date,
            current_period_end=future_date,
            trial_start=past_date,
            trial_end=future_date,
        )
        assert trial_subscription.is_trialing is True
        
        # Expired trial
        expired_trial = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.TRIALING,
            billing_interval=BillingInterval.MONTHLY,
            started_at=past_date,
            current_period_start=past_date,
            current_period_end=future_date,
            trial_start=past_date,
            trial_end=past_date,
        )
        assert expired_trial.is_trialing is False
        
        # No trial end date
        no_trial = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=past_date,
            current_period_start=past_date,
            current_period_end=future_date,
        )
        assert no_trial.is_trialing is False

    def test_subscription_days_until_expiry(self):
        """Test days_until_expiry property"""
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=15)
        past_date = now - timedelta(days=1)
        
        # Future expiry
        subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=future_date,
        )
        # Should be around 15 days (allowing for small time differences in test execution)
        assert 14 <= subscription.days_until_expiry <= 15
        
        # Past expiry
        expired_subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=past_date,
            current_period_start=past_date,
            current_period_end=past_date,
        )
        assert expired_subscription.days_until_expiry == 0

    def test_subscription_usage_limits(self):
        """Test subscription usage limit methods"""
        # Mock plan with limits
        plan = SubscriptionPlan(
            name="Limited Plan",
            plan_type=PlanType.PROFESSIONAL,
            monthly_price=Decimal("10000.00"),
            yearly_price=Decimal("100000.00"),
            max_invoices_per_month=10,
            max_customers=50,
            max_team_members=3,
        )
        
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=30)
        
        subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=future_date,
            current_invoice_count=5,
            current_customer_count=25,
            current_team_member_count=2,
        )
        subscription.plan = plan  # Mock relationship
        
        # Within limits
        assert subscription.can_create_invoice() is True
        assert subscription.can_add_customer() is True
        assert subscription.can_add_team_member() is True
        
        # At limits
        subscription.current_invoice_count = 10
        subscription.current_customer_count = 50
        subscription.current_team_member_count = 3
        
        assert subscription.can_create_invoice() is False
        assert subscription.can_add_customer() is False
        assert subscription.can_add_team_member() is False

    def test_subscription_unlimited_plan(self):
        """Test subscription with unlimited plan"""
        # Mock unlimited plan
        plan = SubscriptionPlan(
            name="Unlimited Plan",
            plan_type=PlanType.ENTERPRISE,
            monthly_price=Decimal("50000.00"),
            yearly_price=Decimal("500000.00"),
            max_invoices_per_month=None,  # Unlimited
            max_customers=None,  # Unlimited
            max_team_members=None,  # Unlimited
        )
        
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=30)
        
        subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=future_date,
            current_invoice_count=1000,
            current_customer_count=5000,
            current_team_member_count=50,
        )
        subscription.plan = plan  # Mock relationship
        
        # Should allow unlimited usage
        assert subscription.can_create_invoice() is True
        assert subscription.can_add_customer() is True
        assert subscription.can_add_team_member() is True

    def test_subscription_extend_trial(self):
        """Test trial extension functionality"""
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=30)
        
        subscription = Subscription(
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=future_date,
        )
        
        # Extend trial for new subscription
        subscription.extend_trial(14)
        assert subscription.trial_start is not None
        assert subscription.trial_end is not None
        assert subscription.status == SubscriptionStatus.TRIALING
        
        # Extend existing trial
        original_trial_end = subscription.trial_end
        subscription.extend_trial(7)
        assert subscription.trial_end > original_trial_end

    def test_usage_record_creation(self):
        """Test UsageRecord model creation"""
        usage_record = UsageRecord(
            subscription_id=1,
            month=8,
            year=2023,
            invoices_created=25,
            customers_created=10,
            team_members_added=2,
            api_calls_made=500,
        )
        
        assert usage_record.subscription_id == 1
        assert usage_record.month == 8
        assert usage_record.year == 2023
        assert usage_record.invoices_created == 25
        assert usage_record.customers_created == 10
        assert usage_record.team_members_added == 2
        assert usage_record.api_calls_made == 500

    def test_plan_type_enum(self):
        """Test PlanType enum values"""
        assert PlanType.FREE.value == "free"
        assert PlanType.PROFESSIONAL.value == "professional"
        assert PlanType.ENTERPRISE.value == "enterprise"

    def test_billing_interval_enum(self):
        """Test BillingInterval enum values"""
        assert BillingInterval.MONTHLY.value == "monthly"
        assert BillingInterval.YEARLY.value == "yearly"

    def test_subscription_status_enum(self):
        """Test SubscriptionStatus enum values"""
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.INACTIVE.value == "inactive"
        assert SubscriptionStatus.CANCELED.value == "canceled"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.TRIALING.value == "trialing"
        assert SubscriptionStatus.PAUSED.value == "paused"