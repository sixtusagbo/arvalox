from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    UsageRecord,
    PlanType,
    BillingInterval,
    SubscriptionStatus,
)
from app.schemas.subscription import (
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionCancelRequest,
    UsageRecordResponse,
    UsageStatsResponse,
    SubscriptionSummaryResponse,
    PlanComparisonResponse,
    TrialExtensionRequest,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get all available subscription plans"""
    plans = await SubscriptionService.get_all_plans(db)
    return plans


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a specific subscription plan"""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        )
    
    return plan


@router.get("/current", response_model=SubscriptionSummaryResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current organization subscription with usage stats"""
    # Get subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization",
        )
    
    # Calculate usage stats
    usage_stats = await _calculate_usage_stats(subscription)
    
    # Get recent usage records (last 3 months)
    now = datetime.utcnow()
    result = await db.execute(
        select(UsageRecord)
        .where(UsageRecord.subscription_id == subscription.id)
        .order_by(UsageRecord.year.desc(), UsageRecord.month.desc())
        .limit(3)
    )
    recent_usage = result.scalars().all()
    
    return SubscriptionSummaryResponse(
        subscription=subscription,
        usage_stats=usage_stats,
        recent_usage=recent_usage,
    )


@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new subscription (admin/owner only)"""
    # Check permissions
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and admins can manage subscriptions"
        )
    
    # Check if organization already has a subscription
    existing_subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization already has an active subscription"
        )
    
    # Verify plan exists
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == request.plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    
    # Create subscription
    subscription = await SubscriptionService.create_subscription(
        db=db,
        organization_id=current_user.organization_id,
        plan_id=request.plan_id,
        billing_interval=request.billing_interval,
        start_trial=request.start_trial,
        trial_days=request.trial_days,
    )
    
    # Load plan for response
    await db.refresh(subscription, ["plan"])
    
    return subscription


@router.put("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    request: SubscriptionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Upgrade/change subscription plan"""
    # Check permissions
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and admins can manage subscriptions"
        )
    
    # Get current subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization"
        )
    
    # If changing plan, verify new plan exists
    if request.plan_id:
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == request.plan_id)
        )
        new_plan = result.scalar_one_or_none()
        
        if not new_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New subscription plan not found"
            )
    
    # Update subscription
    updated_subscription = await SubscriptionService.upgrade_subscription(
        db=db,
        subscription_id=subscription.id,
        new_plan_id=request.plan_id,
        billing_interval=request.billing_interval,
    )
    
    # Update Paystack codes if provided
    if request.paystack_customer_code or request.paystack_subscription_code:
        if request.paystack_customer_code:
            updated_subscription.paystack_customer_code = request.paystack_customer_code
        if request.paystack_subscription_code:
            updated_subscription.paystack_subscription_code = request.paystack_subscription_code
        
        await db.commit()
        await db.refresh(updated_subscription)
    
    # Load plan for response
    await db.refresh(updated_subscription, ["plan"])
    
    return updated_subscription


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    request: SubscriptionCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Cancel subscription"""
    # Check permissions
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and admins can manage subscriptions"
        )
    
    # Get current subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization"
        )
    
    if subscription.status == SubscriptionStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is already canceled"
        )
    
    # Cancel subscription
    canceled_subscription = await SubscriptionService.cancel_subscription(
        db=db,
        subscription_id=subscription.id,
        cancel_immediately=request.cancel_immediately,
    )
    
    # Load plan for response
    await db.refresh(canceled_subscription, ["plan"])
    
    return canceled_subscription


@router.post("/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Reactivate a canceled subscription"""
    # Check permissions
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and admins can manage subscriptions"
        )
    
    # Get current subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization"
        )
    
    if subscription.status != SubscriptionStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only canceled subscriptions can be reactivated"
        )
    
    # Reactivate subscription
    reactivated_subscription = await SubscriptionService.reactivate_subscription(
        db=db,
        subscription_id=subscription.id,
    )
    
    # Load plan for response
    await db.refresh(reactivated_subscription, ["plan"])
    
    return reactivated_subscription


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current usage statistics"""
    # Get subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization"
        )
    
    return await _calculate_usage_stats(subscription)


@router.get("/usage/history", response_model=List[UsageRecordResponse])
async def get_usage_history(
    limit: int = 12,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get usage history"""
    # Get subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization"
        )
    
    # Get usage records
    result = await db.execute(
        select(UsageRecord)
        .where(UsageRecord.subscription_id == subscription.id)
        .order_by(UsageRecord.year.desc(), UsageRecord.month.desc())
        .limit(limit)
    )
    
    return result.scalars().all()


@router.get("/compare", response_model=PlanComparisonResponse)
async def compare_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Compare current plan with other available plans"""
    # Get subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization"
        )
    
    # Get all plans
    all_plans = await SubscriptionService.get_all_plans(db)
    current_plan = subscription.plan
    
    # Categorize plans
    upgrade_options = []
    downgrade_options = []
    
    for plan in all_plans:
        if plan.id == current_plan.id:
            continue
        
        if plan.monthly_price > current_plan.monthly_price:
            upgrade_options.append(plan)
        elif plan.monthly_price < current_plan.monthly_price:
            downgrade_options.append(plan)
    
    return PlanComparisonResponse(
        current_plan=current_plan,
        available_plans=all_plans,
        upgrade_options=upgrade_options,
        downgrade_options=downgrade_options,
    )


@router.post("/extend-trial", response_model=SubscriptionResponse)
async def extend_trial(
    request: TrialExtensionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Extend trial period (admin/owner only)"""
    # Check permissions
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and admins can extend trials"
        )
    
    # Get subscription
    subscription = await SubscriptionService.get_organization_subscription(
        db, current_user.organization_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for organization"
        )
    
    if not subscription.is_trialing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is not in trial period"
        )
    
    # Extend trial
    subscription.extend_trial(request.additional_days)
    await db.commit()
    await db.refresh(subscription)
    
    # Load plan for response
    await db.refresh(subscription, ["plan"])
    
    return subscription


async def _calculate_usage_stats(subscription: Subscription) -> UsageStatsResponse:
    """Helper function to calculate usage statistics"""
    plan = subscription.plan
    
    # Calculate usage percentages
    invoice_usage_percentage = None
    customer_usage_percentage = None
    team_member_usage_percentage = None
    
    if plan.max_invoices_per_month is not None:
        invoice_usage_percentage = (subscription.current_invoice_count / plan.max_invoices_per_month) * 100
    
    if plan.max_customers is not None:
        customer_usage_percentage = (subscription.current_customer_count / plan.max_customers) * 100
    
    if plan.max_team_members is not None:
        team_member_usage_percentage = (subscription.current_team_member_count / plan.max_team_members) * 100
    
    return UsageStatsResponse(
        current_invoice_count=subscription.current_invoice_count,
        current_customer_count=subscription.current_customer_count,
        current_team_member_count=subscription.current_team_member_count,
        max_invoices_per_month=plan.max_invoices_per_month,
        max_customers=plan.max_customers,
        max_team_members=plan.max_team_members,
        invoice_usage_percentage=invoice_usage_percentage,
        customer_usage_percentage=customer_usage_percentage,
        team_member_usage_percentage=team_member_usage_percentage,
        can_create_invoice=subscription.can_create_invoice(),
        can_add_customer=subscription.can_add_customer(),
        can_add_team_member=subscription.can_add_team_member(),
    )