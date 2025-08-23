from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.subscription import PlanType, BillingInterval, SubscriptionStatus


class SubscriptionPlanResponse(BaseModel):
    """Response schema for subscription plans"""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    plan_type: PlanType
    description: Optional[str] = None
    
    # Pricing
    monthly_price: Decimal
    yearly_price: Decimal
    currency: str
    
    # Limits and features
    max_invoices_per_month: Optional[int] = None
    max_customers: Optional[int] = None
    max_team_members: Optional[int] = None
    
    # Feature flags
    custom_branding: bool
    api_access: bool
    advanced_reporting: bool
    priority_support: bool
    multi_currency: bool
    
    # Plan metadata
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class SubscriptionResponse(BaseModel):
    """Response schema for subscriptions"""
    model_config = {"from_attributes": True}
    
    id: int
    organization_id: int
    plan_id: int
    
    status: SubscriptionStatus
    billing_interval: BillingInterval
    
    # Subscription lifecycle
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Payment information
    paystack_customer_code: Optional[str] = None
    paystack_subscription_code: Optional[str] = None
    next_payment_date: Optional[datetime] = None
    
    # Usage tracking
    current_invoice_count: int
    current_customer_count: int
    current_team_member_count: int
    
    # Computed properties
    is_active: bool
    is_trialing: bool
    days_until_expiry: Optional[int]
    
    # Relationships
    plan: SubscriptionPlanResponse
    
    created_at: datetime
    updated_at: datetime


class SubscriptionCreateRequest(BaseModel):
    """Request schema for creating subscriptions"""
    plan_id: int = Field(..., description="ID of the subscription plan")
    billing_interval: BillingInterval = Field(default=BillingInterval.MONTHLY, description="Billing frequency")
    start_trial: bool = Field(default=True, description="Whether to start with a trial period")
    trial_days: int = Field(default=14, ge=1, le=90, description="Number of trial days (1-90)")


class SubscriptionUpdateRequest(BaseModel):
    """Request schema for updating subscriptions"""
    plan_id: Optional[int] = Field(None, description="New plan ID for upgrades/downgrades")
    billing_interval: Optional[BillingInterval] = Field(None, description="New billing interval")
    paystack_customer_code: Optional[str] = Field(None, description="Paystack customer code")
    paystack_subscription_code: Optional[str] = Field(None, description="Paystack subscription code")


class SubscriptionCancelRequest(BaseModel):
    """Request schema for canceling subscriptions"""
    cancel_immediately: bool = Field(default=False, description="Cancel immediately or at period end")
    reason: Optional[str] = Field(None, max_length=500, description="Cancellation reason")


class UsageRecordResponse(BaseModel):
    """Response schema for usage records"""
    model_config = {"from_attributes": True}
    
    id: int
    subscription_id: int
    month: int
    year: int
    
    # Usage counters
    invoices_created: int
    customers_created: int
    team_members_added: int
    api_calls_made: int
    
    created_at: datetime
    updated_at: datetime


class UsageStatsResponse(BaseModel):
    """Response schema for current usage statistics"""
    
    # Current period usage
    current_invoice_count: int
    current_customer_count: int
    current_team_member_count: int
    
    # Plan limits
    max_invoices_per_month: Optional[int] = None
    max_customers: Optional[int] = None
    max_team_members: Optional[int] = None
    
    # Computed usage percentages (0-100, None if unlimited)
    invoice_usage_percentage: Optional[float] = None
    customer_usage_percentage: Optional[float] = None
    team_member_usage_percentage: Optional[float] = None
    
    # Can perform actions
    can_create_invoice: bool
    can_add_customer: bool
    can_add_team_member: bool


class SubscriptionSummaryResponse(BaseModel):
    """Summary response combining subscription and usage info"""
    
    subscription: SubscriptionResponse
    usage_stats: UsageStatsResponse
    recent_usage: List[UsageRecordResponse]


class PlanComparisonResponse(BaseModel):
    """Response for plan comparison"""
    
    current_plan: SubscriptionPlanResponse
    available_plans: List[SubscriptionPlanResponse]
    upgrade_options: List[SubscriptionPlanResponse]
    downgrade_options: List[SubscriptionPlanResponse]


class TrialExtensionRequest(BaseModel):
    """Request schema for extending trial"""
    additional_days: int = Field(..., ge=1, le=30, description="Additional trial days (1-30)")
    reason: Optional[str] = Field(None, max_length=200, description="Extension reason")


class BillingHistoryResponse(BaseModel):
    """Response schema for billing history"""
    
    period_start: datetime
    period_end: datetime
    amount: Decimal
    currency: str
    status: str
    paid_at: Optional[datetime] = None
    invoice_url: Optional[str] = None
    
    # Usage during this period
    invoices_created: int
    customers_created: int
    team_members_added: int