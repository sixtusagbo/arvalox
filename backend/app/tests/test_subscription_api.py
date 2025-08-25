import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.dependencies import get_current_user
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

    @pytest.fixture(autouse=True)
    def setup_auth(self, mock_current_user):
        """Set up authentication override for all tests"""
        def get_mock_user():
            return mock_current_user
        
        app.dependency_overrides[get_current_user] = get_mock_user
        yield
        app.dependency_overrides.clear()

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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def mock_subscription(self, mock_subscription_plan):
        """Mock subscription"""
        now = datetime.now(timezone.utc)
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
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

    @pytest.mark.asyncio
    async def test_get_subscription_plan_not_found(self, client: AsyncClient):
        """Test getting non-existent subscription plan"""
        response = await client.get("/api/v1/subscriptions/plans/999")
        assert response.status_code == 404
        assert "Subscription plan not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_subscription(self, mock_current_user, mock_subscription, client: AsyncClient):
        """Test getting current organization subscription"""
        with patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription:
            mock_get_subscription.return_value = mock_subscription
            response = await client.get("/api/v1/subscriptions/current")

        assert response.status_code == 200
        data = response.json()
        assert data["subscription"]["id"] == 1
        assert data["subscription"]["organization_id"] == 1
        assert data["usage_stats"]["current_invoice_count"] == 25
        assert data["usage_stats"]["can_create_invoice"] is True

    @pytest.mark.asyncio
    async def test_get_current_subscription_not_found(self, mock_current_user, client: AsyncClient):
        """Test getting current subscription when none exists"""
        with patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription:
            mock_get_subscription.return_value = None
            response = await client.get("/api/v1/subscriptions/current")

        assert response.status_code == 404
        assert "No subscription found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_subscription(self, mock_current_user, mock_subscription_plan, client: AsyncClient):
        """Test creating a new subscription"""
        request_data = {
            "plan_id": 2,
            "billing_interval": "monthly", 
            "start_trial": True,
            "trial_days": 14
        }

        now = datetime.now(timezone.utc)
        mock_subscription = Subscription(
            id=1,
            organization_id=1,
            plan_id=2,
            status=SubscriptionStatus.TRIALING,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            current_invoice_count=0,
            current_customer_count=0,
            current_team_member_count=1,
            created_at=now,
            updated_at=now,
        )
        mock_subscription.plan = mock_subscription_plan

        # Set up database session to return our mock plan
        def mock_db_session():
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_subscription_plan
            mock_db.execute.return_value = mock_result
            return mock_db
        
        # Override get_db to return our mocked database session
        from app.core.database import get_db
        app.dependency_overrides[get_db] = mock_db_session

        with patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_existing, \
             patch("app.services.subscription_service.SubscriptionService.create_subscription") as mock_create:

            mock_get_existing.return_value = None  # No existing subscription
            mock_create.return_value = mock_subscription

            response = await client.post("/api/v1/subscriptions/create", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["organization_id"] == 1
            assert data["plan_id"] == 2
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

    @pytest.mark.asyncio
    async def test_create_subscription_permission_denied(self, client: AsyncClient):
        """Test creating subscription without proper permissions"""
        # Override the mock user for this specific test
        mock_user = User(
            id=1,
            role="sales_rep",
            organization_id=1,
        )
        
        def get_mock_sales_rep_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_mock_sales_rep_user
        
        request_data = {
            "plan_id": 1,
            "billing_interval": "monthly"
        }

        response = await client.post("/api/v1/subscriptions/create", json=request_data)

        assert response.status_code == 403
        assert "Only organization owners and admins" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upgrade_subscription(self, mock_current_user, mock_subscription, mock_subscription_plan, client: AsyncClient):
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
            yearly_price=Decimal("350000.00"),
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Create updated subscription with all required fields
        now = datetime.now(timezone.utc)
        updated_subscription = Subscription(
            id=1,
            organization_id=1,
            plan_id=2,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.YEARLY,
            started_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=365),
            current_invoice_count=25,
            current_customer_count=100,
            current_team_member_count=3,
            created_at=now,
            updated_at=now,
        )
        updated_subscription.plan = new_plan

        # Set up database session to return our mock plan and subscription
        def mock_db_session():
            mock_db = AsyncMock()
            mock_result = MagicMock()
            # For the plan lookup in the API, return the new plan
            mock_result.scalar_one_or_none.return_value = new_plan
            mock_db.execute.return_value = mock_result
            return mock_db
        
        # Override get_db to return our mocked database session
        from app.core.database import get_db
        app.dependency_overrides[get_db] = mock_db_session

        with patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription, \
             patch("app.services.subscription_service.SubscriptionService.update_subscription_with_usage_reset") as mock_update:

            mock_get_subscription.return_value = mock_subscription
            mock_update.return_value = updated_subscription

            response = await client.put("/api/v1/subscriptions/upgrade", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["plan_id"] == 2
            assert data["billing_interval"] == "yearly"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, mock_current_user, mock_subscription, client: AsyncClient):
        """Test canceling subscription"""
        request_data = {
            "cancel_immediately": False,
            "reason": "Switching to different solution"
        }

        # Create properly structured canceled subscription
        now = datetime.now(timezone.utc)
        canceled_subscription = Subscription(
            id=1,
            organization_id=1,
            plan_id=1,
            status=SubscriptionStatus.CANCELED,
            billing_interval=BillingInterval.MONTHLY,
            started_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            canceled_at=now,
            current_invoice_count=25,
            current_customer_count=100,
            current_team_member_count=3,
            created_at=now,
            updated_at=now,
        )
        canceled_subscription.plan = mock_subscription.plan

        # Set up database session to mock refresh call
        def mock_db_session():
            mock_db = AsyncMock()
            # Mock refresh to do nothing
            mock_db.refresh = AsyncMock()
            return mock_db
        
        # Override get_db to return our mocked database session
        from app.core.database import get_db
        app.dependency_overrides[get_db] = mock_db_session

        with patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription, \
             patch("app.services.subscription_service.SubscriptionService.cancel_subscription") as mock_cancel:

            mock_get_subscription.return_value = mock_subscription
            mock_cancel.return_value = canceled_subscription

            response = await client.post("/api/v1/subscriptions/cancel", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "canceled"
            assert data["canceled_at"] is not None

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, mock_current_user, mock_subscription, client: AsyncClient):
        """Test getting usage statistics"""
        with patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription:

            mock_get_subscription.return_value = mock_subscription

            response = await client.get("/api/v1/subscriptions/usage")

            assert response.status_code == 200
            data = response.json()
            assert data["current_invoice_count"] == 25
            assert data["current_customer_count"] == 100
            assert data["max_invoices_per_month"] == 500
            assert data["can_create_invoice"] is True

    @pytest.mark.asyncio
    async def test_compare_plans(self, mock_current_user, mock_subscription, client: AsyncClient):
        """Test comparing subscription plans"""
        now = datetime.now(timezone.utc)
        all_plans = [
            SubscriptionPlan(
                id=1,
                name="Free Plan",
                plan_type=PlanType.FREE,
                monthly_price=Decimal("0.00"),
                yearly_price=Decimal("0.00"),
                currency="NGN",
                max_invoices_per_month=10,
                max_customers=50,
                max_team_members=1,
                custom_branding=False,
                api_access=False,
                advanced_reporting=False,
                priority_support=False,
                multi_currency=False,
                is_active=True,
                sort_order=1,
                created_at=now,
                updated_at=now,
            ),
            SubscriptionPlan(
                id=2,
                name="Professional Plan",
                plan_type=PlanType.PROFESSIONAL,
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
                created_at=now,
                updated_at=now,
            ),
            SubscriptionPlan(
                id=3,
                name="Enterprise Plan",
                plan_type=PlanType.ENTERPRISE,
                monthly_price=Decimal("50000.00"),
                yearly_price=Decimal("500000.00"),
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
                sort_order=3,
                created_at=now,
                updated_at=now,
            ),
        ]

        with patch("app.services.subscription_service.SubscriptionService.get_organization_subscription") as mock_get_subscription, \
             patch("app.services.subscription_service.SubscriptionService.get_all_plans") as mock_get_plans:

            mock_get_subscription.return_value = mock_subscription
            mock_get_plans.return_value = all_plans

            response = await client.get("/api/v1/subscriptions/compare")

            assert response.status_code == 200
            data = response.json()
            assert data["current_plan"]["name"] == "Professional Plan"
            assert len(data["available_plans"]) == 3
            assert len(data["upgrade_options"]) == 1  # Enterprise plan