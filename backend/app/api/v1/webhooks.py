import json
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.subscription import Subscription, SubscriptionStatus
from app.services.paystack_service import PaystackService

router = APIRouter()


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Handle Paystack webhooks"""
    
    # Get raw body
    body = await request.body()
    
    # Verify webhook signature
    paystack = PaystackService()
    signature = request.headers.get("x-paystack-signature", "")
    
    if not paystack.verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse payload
    try:
        payload = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    event = payload.get("event")
    data = payload.get("data", {})
    
    try:
        if event == "charge.success":
            await handle_charge_success(db, data)
        elif event == "subscription.create":
            await handle_subscription_create(db, data)
        elif event == "subscription.disable":
            await handle_subscription_disable(db, data)
        elif event == "invoice.create":
            await handle_invoice_create(db, data)
        elif event == "invoice.payment_failed":
            await handle_invoice_payment_failed(db, data)
        # Add more event handlers as needed
        
        return {"status": "success"}
        
    except Exception as e:
        # Log error but return success to Paystack to avoid retries
        print(f"Webhook processing error: {str(e)}")
        return {"status": "error", "message": str(e)}


async def handle_charge_success(db: AsyncSession, data: dict):
    """Handle successful charge"""
    customer_code = data.get("customer", {}).get("customer_code")
    reference = data.get("reference")
    amount = data.get("amount")  # In kobo
    
    if not customer_code:
        return
    
    # Find subscription by customer code
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.paystack_customer_code == customer_code)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        # Update subscription status if it was in trial or inactive
        if subscription.status in [SubscriptionStatus.TRIALING, SubscriptionStatus.INACTIVE]:
            subscription.status = SubscriptionStatus.ACTIVE
            
        # Update next payment date based on billing interval
        now = datetime.now(timezone.utc)
        if subscription.billing_interval.value == "monthly":
            from datetime import timedelta
            subscription.next_payment_date = now + timedelta(days=30)
        else:
            subscription.next_payment_date = now + timedelta(days=365)
            
        await db.commit()


async def handle_subscription_create(db: AsyncSession, data: dict):
    """Handle subscription creation"""
    customer_code = data.get("customer", {}).get("customer_code")
    subscription_code = data.get("subscription_code")
    
    if not customer_code or not subscription_code:
        return
    
    # Find subscription by customer code
    result = await db.execute(
        select(Subscription)
        .where(Subscription.paystack_customer_code == customer_code)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.paystack_subscription_code = subscription_code
        subscription.status = SubscriptionStatus.ACTIVE
        await db.commit()


async def handle_subscription_disable(db: AsyncSession, data: dict):
    """Handle subscription disable/cancel"""
    subscription_code = data.get("subscription_code")
    
    if not subscription_code:
        return
    
    # Find subscription by subscription code
    result = await db.execute(
        select(Subscription)
        .where(Subscription.paystack_subscription_code == subscription_code)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.now(timezone.utc)
        await db.commit()


async def handle_invoice_create(db: AsyncSession, data: dict):
    """Handle invoice creation from Paystack"""
    # This is when Paystack creates an invoice for recurring billing
    customer_code = data.get("customer", {}).get("customer_code")
    
    if not customer_code:
        return
    
    # Find subscription and possibly send notification
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.organization))
        .where(Subscription.paystack_customer_code == customer_code)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        # Could send email notification about upcoming payment
        pass


async def handle_invoice_payment_failed(db: AsyncSession, data: dict):
    """Handle failed invoice payment"""
    customer_code = data.get("customer", {}).get("customer_code")
    
    if not customer_code:
        return
    
    # Find subscription and update status
    result = await db.execute(
        select(Subscription)
        .where(Subscription.paystack_customer_code == customer_code)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.status = SubscriptionStatus.PAST_DUE
        await db.commit()
        
        # Could send email notification about failed payment