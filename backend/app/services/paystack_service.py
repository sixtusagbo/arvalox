import hashlib
import hmac
from decimal import Decimal
from typing import Any

import aiohttp
from datetime import datetime

from app.core.config import settings
from app.models.subscription import SubscriptionPlan, BillingInterval


class PaystackService:
    """Service for Paystack payment integration"""
    
    def __init__(self):
        self.secret_key = settings.paystack_secret_key
        self.public_key = settings.paystack_public_key
        self.webhook_secret = settings.paystack_webhook_secret
        self.base_url = "https://api.paystack.co"
        
    def _get_headers(self) -> dict[str, str]:
        """Get headers for Paystack API requests"""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    async def initialize_transaction(
        self,
        email: str,
        amount: Decimal,
        plan_id: int,
        organization_name: str,
        billing_interval: BillingInterval,
        callback_url: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Initialize a Paystack transaction for subscription payment"""
        
        # Convert amount to kobo (Paystack uses kobo for NGN)
        amount_kobo = int(amount * 100)
        
        payload = {
            "email": email,
            "amount": amount_kobo,
            "currency": "NGN",
            "callback_url": callback_url,
            "metadata": {
                "plan_id": plan_id,
                "billing_interval": billing_interval.value,
                "organization_name": organization_name,
                **(metadata or {})
            },
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"]
        }
        
        async with aiohttp.ClientSession() as session, session.post(
            f"{self.base_url}/transaction/initialize",
            headers=self._get_headers(),
            json=payload
        ) as response:
                result = await response.json()
                
                if not result.get("status"):
                    raise Exception(f"Paystack initialization failed: {result.get('message')}")
                    
                return result["data"]

    async def verify_transaction(self, reference: str) -> dict[str, Any]:
        """Verify a Paystack transaction"""
        
        async with aiohttp.ClientSession() as session, session.get(
            f"{self.base_url}/transaction/verify/{reference}",
            headers=self._get_headers()
        ) as response:
                result = await response.json()
                
                if not result.get("status"):
                    raise Exception(f"Transaction verification failed: {result.get('message')}")
                    
                return result["data"]

    async def create_subscription_plan(
        self,
        plan: SubscriptionPlan,
        billing_interval: BillingInterval
    ) -> dict[str, Any]:
        """Create a subscription plan on Paystack"""
        
        # Determine amount based on billing interval
        if billing_interval == BillingInterval.MONTHLY:
            amount = plan.monthly_price
            interval = "monthly"
        else:
            amount = plan.yearly_price
            interval = "annually"
            
        # Convert to kobo
        amount_kobo = int(amount * 100)
        
        payload = {
            "name": f"{plan.name} - {billing_interval.value.title()}",
            "amount": amount_kobo,
            "interval": interval,
            "currency": "NGN",
            "description": plan.description,
            "send_invoices": True,
            "send_sms": True,
        }
        
        async with aiohttp.ClientSession() as session, session.post(
            f"{self.base_url}/plan",
            headers=self._get_headers(),
            json=payload
        ) as response:
                result = await response.json()
                
                if not result.get("status"):
                    raise Exception(f"Plan creation failed: {result.get('message')}")
                    
                return result["data"]

    async def create_subscription(
        self,
        customer_code: str,
        plan_code: str,
        authorization_code: str,
        start_date: datetime | None = None
    ) -> dict[str, Any]:
        """Create a subscription for a customer"""
        
        payload = {
            "customer": customer_code,
            "plan": plan_code,
            "authorization": authorization_code,
        }
        
        if start_date:
            payload["start_date"] = start_date.isoformat()
        
        async with aiohttp.ClientSession() as session, session.post(
            f"{self.base_url}/subscription",
            headers=self._get_headers(),
            json=payload
        ) as response:
                result = await response.json()
                
                if not result.get("status"):
                    raise Exception(f"Subscription creation failed: {result.get('message')}")
                    
                return result["data"]

    async def cancel_subscription(self, subscription_code: str, token: str) -> dict[str, Any]:
        """Cancel a subscription"""
        
        payload = {
            "code": subscription_code,
            "token": token
        }
        
        async with aiohttp.ClientSession() as session, session.post(
            f"{self.base_url}/subscription/disable",
            headers=self._get_headers(),
            json=payload
        ) as response:
                result = await response.json()
                
                if not result.get("status"):
                    raise Exception(f"Subscription cancellation failed: {result.get('message')}")
                    
                return result["data"]

    async def create_customer(self, email: str, first_name: str, last_name: str) -> dict[str, Any]:
        """Create a customer on Paystack"""
        
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
        
        async with aiohttp.ClientSession() as session, session.post(
            f"{self.base_url}/customer",
            headers=self._get_headers(),
            json=payload
        ) as response:
                result = await response.json()
                
                if not result.get("status"):
                    raise Exception(f"Customer creation failed: {result.get('message')}")
                    
                return result["data"]

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Paystack"""
        
        computed_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)

    def format_amount(self, kobo_amount: int) -> Decimal:
        """Convert kobo amount to Naira"""
        return Decimal(kobo_amount) / 100