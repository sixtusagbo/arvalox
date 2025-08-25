import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    PlanType,
    BillingInterval,
    SubscriptionStatus,
)
from app.models.user import User
from app.models.organization import Organization


class TestSubscriptionAPI:
    """Test subscription API endpoints"""

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user"""
        user = User(
            id=1,
            email="owner@test.com",
            first_name="Test",
            last_name="Owner",
            role="owner",
            organization_id=1,
            is_active=True,
        )
        return user

    @pytest.fixture
    def mock_subscription_plan(self):
        """Mock subscription plan"""
        return SubscriptionPlan(
            id=2,
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
            is_active=True,
            sort_order=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    @pytest.fixture
    def mock_subscription(self, mock_subscription_plan):
        """Mock subscription"""
        now = datetime.utcnow()
        subscription = Subscription(
            id=1,
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            current_invoice_count=25,
            current_customer_count=100,
            current_team_member_count=3,
            created_at=now,
            updated_at=now,
        )
        subscription.plan = mock_subscription_plan
        return subscription

    def test_get_subscription_plans(self):
        """Test getting all subscription plans"""
        mock_plans = [
            SubscriptionPlan(
                id=1,
                name="Free Plan",
                plan_type=PlanType.FREE,
                monthly_price=Decimal("0.00"),
                yearly_price=Decimal("0.00"),
                currency="NGN",
                is_active=True,
                sort_order=1,
                custom_branding=False,
                api_access=False,
                advanced_reporting=False,
                priority_support=False,
                multi_currency=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            SubscriptionPlan(
                id=2,
                name="Professional Plan",
                plan_type=PlanType.PROFESSIONAL,
                monthly_price=Decimal("15000.00"),
                yearly_price=Decimal("150000.00"),
                currency="NGN",
                is_active=True,
                sort_order=2,
                custom_branding=False,
                api_access=True,
                advanced_reporting=True,
                priority_support=False,
                multi_currency=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        with patch("app.services.subscription_service.SubscriptionService.get_all_plans") as mock_get_plans:
            mock_get_plans.return_value = mock_plans

            with TestClient(app) as client:
                response = client.get("/api/v1/subscriptions/plans")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Free Plan"
            assert data[0]["monthly_price"] == "0.00"
            assert data[1]["name"] == "Professional Plan"
            assert data[1]["monthly_price"] == "15000.00"

    def test_get_subscription_plan_by_id(self, mock_subscription_plan):
        """Test getting a specific subscription plan"""
        with patch("app.core.dependencies.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_subscription_plan
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            with TestClient(app) as client:
                response = client.get("/api/v1/subscriptions/plans/2")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 2
            assert data["name"] == "Professional Plan"
            assert data["monthly_price"] == "25000.00"

    def test_get_subscription_plan_not_found(self):
        """Test getting non-existent subscription plan"""
        with patch("app.core.dependencies.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            with TestClient(app) as client:
                response = client.get("/api/v1/subscriptions/plans/999")

            assert response.status_code == 404
            assert "Subscription plan not found" in response.json()["detail"]

    def test_get_current_subscription(self, mock_current_user, mock_subscription):
        """Test getting current organization subscription"""
        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription, \
             patch("app.core.dependencies.get_db") as mock_get_db:

            mock_get_user.return_value = mock_current_user
            mock_get_subscription.return_value = mock_subscription
            
            # Mock database for usage records
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            with TestClient(app) as client:
                response = client.get("/api/v1/subscriptions/current")

            assert response.status_code == 200
            data = response.json()
            assert data["subscription"]["id"] == 1
            assert data["subscription"]["organization_id"] == 1
            assert data["usage_stats"]["current_invoice_count"] == 25
            assert data["usage_stats"]["can_create_invoice"] is True

    def test_get_current_subscription_not_found(self, mock_current_user):
        """Test getting current subscription when none exists"""
        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription:

            mock_get_user.return_value = mock_current_user
            mock_get_subscription.return_value = None

            with TestClient(app) as client:
                response = client.get("/api/v1/subscriptions/current")

            assert response.status_code == 404
            assert "No subscription found" in response.json()["detail"]

    def test_create_subscription(self, mock_current_user, mock_subscription_plan):
        """Test creating a new subscription"""
        request_data = {
            "plan_id": 1,
            "billing_interval": "monthly",
            "start_trial": True,
            "trial_days": 14
        }

        mock_subscription = Subscription(
            id=1,
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.TRIALING,
            billing_interval=BillingInterval.MONTHLY,
            started_at=datetime.utcnow(),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
        )
        mock_subscription.plan = mock_subscription_plan

        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_existing, \
             patch("app.services.subscription_service.SubscriptionService.create_subscription") as mock_create, \
             patch("app.core.dependencies.get_db") as mock_get_db:

            mock_get_user.return_value = mock_current_user
            mock_get_existing.return_value = None  # No existing subscription
            mock_create.return_value = mock_subscription

            # Mock database for plan lookup
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_subscription_plan
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            with TestClient(app) as client:
                response = client.post("/api/v1/subscriptions/create", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["organization_id"] == 1
            assert data["plan_id"] == 1
            assert data["status"] == "trialing"

    def test_create_subscription_already_exists(self, mock_current_user, mock_subscription):
        """Test creating subscription when one already exists"""
        request_data = {
            "plan_id": 1,
            "billing_interval": "monthly"
        }

        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_existing:

            mock_get_user.return_value = mock_current_user
            mock_get_existing.return_value = mock_subscription

            with TestClient(app) as client:
                response = client.post("/api/v1/subscriptions/create", json=request_data)

            assert response.status_code == 400
            assert "already has an active subscription" in response.json()["detail"]

    def test_create_subscription_permission_denied(self):
        """Test creating subscription without proper permissions"""
        request_data = {
            "plan_id": 1,
            "billing_interval": "monthly"
        }

        # Mock user without owner/admin role
        mock_user = User(
            id=1,
            role="sales_rep",
            organization_id=1,
        )

        with patch("app.core.dependencies.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with TestClient(app) as client:
                response = client.post("/api/v1/subscriptions/create", json=request_data)

            assert response.status_code == 403
            assert "Only organization owners and admins" in response.json()["detail"]

    def test_upgrade_subscription(self, mock_current_user, mock_subscription, mock_subscription_plan):
        """Test upgrading subscription"""
        request_data = {
            "plan_id": 2,
            "billing_interval": "yearly"
        }

        # Mock new plan
        new_plan = SubscriptionPlan(
            id=2,
            name="Professional Plan",
            plan_type=PlanType.PROFESSIONAL,
            monthly_price=Decimal("35000.00"),
        )

        updated_subscription = mock_subscription
        updated_subscription.plan_id = 2
        updated_subscription.billing_interval = BillingInterval.YEARLY

        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription, \
             patch("app.services.subscription_service.SubscriptionService.upgrade_subscription") as mock_upgrade, \
             patch("app.core.dependencies.get_db") as mock_get_db:

            mock_get_user.return_value = mock_current_user
            mock_get_subscription.return_value = mock_subscription
            mock_upgrade.return_value = updated_subscription

            # Mock database for plan lookup
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = new_plan
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            with TestClient(app) as client:
                response = client.put("/api/v1/subscriptions/upgrade", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["plan_id"] == 2
            assert data["billing_interval"] == "yearly"

    def test_cancel_subscription(self, mock_current_user, mock_subscription):
        """Test canceling subscription"""
        request_data = {
            "cancel_immediately": False,
            "reason": "Switching to different solution"
        }

        canceled_subscription = mock_subscription
        canceled_subscription.status = SubscriptionStatus.CANCELED
        canceled_subscription.canceled_at = datetime.utcnow()

        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription, \
             patch("app.services.subscription_service.SubscriptionService.cancel_subscription") as mock_cancel, \
             patch("app.core.dependencies.get_db") as mock_get_db:

            mock_get_user.return_value = mock_current_user
            mock_get_subscription.return_value = mock_subscription
            mock_cancel.return_value = canceled_subscription
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db

            with TestClient(app) as client:
                response = client.post("/api/v1/subscriptions/cancel", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "canceled"
            assert data["canceled_at"] is not None

    def test_get_usage_stats(self, mock_current_user, mock_subscription):
        """Test getting usage statistics"""
        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription:

            mock_get_user.return_value = mock_current_user
            mock_get_subscription.return_value = mock_subscription

            with TestClient(app) as client:
                response = client.get("/api/v1/subscriptions/usage")

            assert response.status_code == 200
            data = response.json()
            assert data["current_invoice_count"] == 25
            assert data["current_customer_count"] == 100
            assert data["max_invoices_per_month"] == 100
            assert data["can_create_invoice"] is True

    def test_compare_plans(self, mock_current_user, mock_subscription):
        """Test comparing subscription plans"""
        all_plans = [
            SubscriptionPlan(
                id=1,
                name="Professional Plan",
                plan_type=PlanType.PROFESSIONAL,
                monthly_price=Decimal("15000.00"),
            ),
            SubscriptionPlan(
                id=2,
                name="Professional",
                plan_type=PlanType.PROFESSIONAL,
                monthly_price=Decimal("35000.00"),
            ),
        ]

        with patch("app.core.dependencies.get_current_user") as mock_get_user, \
             patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription, \
             patch("app.services.subscription_service.SubscriptionService.get_all_plans") as mock_get_plans:

            mock_get_user.return_value = mock_current_user
            mock_get_subscription.return_value = mock_subscription
            mock_get_plans.return_value = all_plans

            with TestClient(app) as client:
                response = client.get("/api/v1/subscriptions/compare")

            assert response.status_code == 200
            data = response.json()
            assert data["current_plan"]["name"] == "Professional Plan"
            assert len(data["available_plans"]) == 2
            assert len(data["upgrade_options"]) == 1  # Professional plan