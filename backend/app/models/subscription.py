from enum import Enum
from typing import Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PlanType(str, Enum):
    """Subscription plan types"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class BillingInterval(str, Enum):
    """Billing intervals"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    """Subscription statuses"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PAUSED = "paused"


class SubscriptionPlan(BaseModel):
    """Subscription plan definitions"""
    __tablename__ = "subscription_plans"

    name = Column(String(100), nullable=False, unique=True)
    plan_type = Column(SQLEnum(PlanType), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Pricing
    monthly_price = Column(Numeric(10, 2), nullable=False, default=0)
    yearly_price = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="NGN")
    
    # Limits and features
    max_invoices_per_month = Column(Integer, nullable=True)  # None = unlimited
    max_customers = Column(Integer, nullable=True)  # None = unlimited
    max_team_members = Column(Integer, nullable=True)  # None = unlimited
    
    # Feature flags
    custom_branding = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    advanced_reporting = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    multi_currency = Column(Boolean, default=False)
    
    # Paystack integration
    paystack_plan_code_monthly = Column(String(100), nullable=True)
    paystack_plan_code_yearly = Column(String(100), nullable=True)
    
    # Plan metadata
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(BaseModel):
    """Organization subscriptions"""
    __tablename__ = "subscriptions"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, unique=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    billing_interval = Column(SQLEnum(BillingInterval), nullable=False, default=BillingInterval.MONTHLY)
    
    # Subscription lifecycle
    started_at = Column(DateTime(timezone=True), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Payment information
    paystack_customer_code = Column(String(100), nullable=True)
    paystack_subscription_code = Column(String(100), nullable=True)
    next_payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    current_invoice_count = Column(Integer, default=0)
    current_customer_count = Column(Integer, default=0)
    current_team_member_count = Column(Integer, default=1)  # Owner counts as 1
    
    # Grace period for downgrades
    downgrade_to_plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    downgrade_effective_date = Column(DateTime(timezone=True), nullable=True)
    
    # Usage reset tracking
    last_invoice_reset_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="subscription")
    plan = relationship("SubscriptionPlan", foreign_keys=[plan_id], back_populates="subscriptions")
    downgrade_plan = relationship("SubscriptionPlan", foreign_keys=[downgrade_to_plan_id])
    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status == SubscriptionStatus.ACTIVE and datetime.now(timezone.utc) <= self.current_period_end


    @property
    def is_trialing(self) -> bool:
        """Check if subscription is in trial period"""
        if not self.trial_end:
            return False
        return self.status == SubscriptionStatus.TRIALING and datetime.now(timezone.utc) <= self.trial_end

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until subscription expires"""
        if not self.current_period_end:
            return None
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)

    def can_create_invoice(self) -> bool:
        """Check if organization can create more invoices"""
        if not self.is_active and not self.is_trialing:
            return False
        
        max_invoices = self.plan.max_invoices_per_month
        if max_invoices is None:  # Unlimited
            return True
        
        return self.current_invoice_count < max_invoices

    def can_add_customer(self) -> bool:
        """Check if organization can add more customers"""
        if not self.is_active and not self.is_trialing:
            return False
        
        max_customers = self.plan.max_customers
        if max_customers is None:  # Unlimited
            return True
        
        return self.current_customer_count < max_customers

    def can_add_team_member(self) -> bool:
        """Check if organization can add more team members"""
        if not self.is_active and not self.is_trialing:
            return False
        
        max_team_members = self.plan.max_team_members
        if max_team_members is None:  # Unlimited
            return True
        
        return self.current_team_member_count < max_team_members

    def extend_trial(self, days: int = 14) -> None:
        """Extend trial period"""
        if self.trial_end:
            self.trial_end += timedelta(days=days)
        else:
            self.trial_start = datetime.now(timezone.utc)
            self.trial_end = datetime.now(timezone.utc) + timedelta(days=days)
            self.status = SubscriptionStatus.TRIALING

    @property
    def is_downgrading(self) -> bool:
        """Check if subscription is scheduled for downgrade"""
        return (self.downgrade_to_plan_id is not None and 
                self.downgrade_effective_date is not None and
                datetime.now(timezone.utc) < self.downgrade_effective_date)

    @property
    def downgrade_days_remaining(self) -> Optional[int]:
        """Get days until downgrade takes effect"""
        if not self.is_downgrading or not self.downgrade_effective_date:
            return None
        delta = self.downgrade_effective_date - datetime.now(timezone.utc)
        return max(0, delta.days)

    def get_effective_plan(self) -> "SubscriptionPlan":
        """Get the plan that should be used for limit checking during grace period"""
        if self.is_downgrading:
            # During grace period, keep current plan benefits
            return self.plan
        return self.plan

    def schedule_downgrade(self, target_plan_id: int) -> None:
        """Schedule downgrade at end of current billing period"""
        self.downgrade_to_plan_id = target_plan_id
        self.downgrade_effective_date = self.current_period_end

    def cancel_downgrade(self) -> None:
        """Cancel scheduled downgrade"""
        self.downgrade_to_plan_id = None
        self.downgrade_effective_date = None

    def apply_downgrade(self) -> bool:
        """Apply scheduled downgrade if due"""
        if not self.is_downgrading:
            return False
        
        now = datetime.now(timezone.utc)
        if now >= self.downgrade_effective_date:
            self.plan_id = self.downgrade_to_plan_id
            self.downgrade_to_plan_id = None
            self.downgrade_effective_date = None
            return True
        return False

    def reset_monthly_usage_if_needed(self) -> bool:
        """Reset invoice count if new billing period started"""
        now = datetime.now(timezone.utc)
        
        # Initialize reset date if not set
        if not self.last_invoice_reset_date:
            self.last_invoice_reset_date = self.current_period_start
            return False
        
        # Check if current period started after last reset
        if self.current_period_start > self.last_invoice_reset_date:
            self.current_invoice_count = 0
            self.last_invoice_reset_date = self.current_period_start
            return True
        return False

    def increment_invoice_count(self) -> None:
        """Increment invoice count and reset if needed"""
        self.reset_monthly_usage_if_needed()
        self.current_invoice_count += 1

    def increment_customer_count(self) -> None:
        """Increment customer count (cumulative)"""
        self.current_customer_count += 1

    def increment_team_member_count(self) -> None:
        """Increment team member count (cumulative)"""
        self.current_team_member_count += 1


class UsageRecord(BaseModel):
    """Monthly usage tracking"""
    __tablename__ = "usage_records"

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    
    # Usage counters
    invoices_created = Column(Integer, default=0)
    customers_created = Column(Integer, default=0)
    team_members_added = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    
    # Relationship
    subscription = relationship("Subscription", back_populates="usage_records")

    class Meta:
        unique_together = [["subscription_id", "month", "year"]]
