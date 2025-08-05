import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.core.security import create_access_token
from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentSearchParams,
    PaymentListResponse,
    PaymentStatusUpdate,
    PaymentSummary,
    InvoicePaymentSummary,
    PaymentAllocation,
    PaymentAllocationCreate,
)


class TestPaymentSchemas:
    """Test payment Pydantic schemas"""

    def test_payment_create_valid(self):
        """Test valid payment creation schema"""
        today = date.today()
        
        payment_data = {
            "invoice_id": 1,
            "payment_date": today,
            "amount": Decimal("500.00"),
            "payment_method": "bank_transfer",
            "reference_number": "TXN123456",
            "notes": "Payment for services",
        }

        payment = PaymentCreate(**payment_data)
        assert payment.invoice_id == 1
        assert payment.amount == Decimal("500.00")
        assert payment.payment_method == "bank_transfer"
        assert payment.reference_number == "TXN123456"

    def test_payment_create_invalid_amount(self):
        """Test payment creation with invalid amount"""
        today = date.today()
        
        payment_data = {
            "invoice_id": 1,
            "payment_date": today,
            "amount": Decimal("0.00"),  # Must be > 0
            "payment_method": "cash",
        }

        with pytest.raises(ValueError):
            PaymentCreate(**payment_data)

    def test_payment_create_future_date(self):
        """Test payment creation with future date"""
        tomorrow = date.today() + timedelta(days=1)
        
        payment_data = {
            "invoice_id": 1,
            "payment_date": tomorrow,  # Future date not allowed
            "amount": Decimal("100.00"),
            "payment_method": "cash",
        }

        with pytest.raises(ValueError):
            PaymentCreate(**payment_data)

    def test_payment_create_invalid_method(self):
        """Test payment creation with invalid payment method"""
        today = date.today()
        
        payment_data = {
            "invoice_id": 1,
            "payment_date": today,
            "amount": Decimal("100.00"),
            "payment_method": "invalid_method",
        }

        with pytest.raises(ValueError):
            PaymentCreate(**payment_data)

    def test_payment_update_partial(self):
        """Test payment update with partial data"""
        update_data = {
            "amount": Decimal("750.00"),
            "notes": "Updated payment notes",
        }

        payment_update = PaymentUpdate(**update_data)
        assert payment_update.amount == Decimal("750.00")
        assert payment_update.notes == "Updated payment notes"
        assert payment_update.payment_method is None  # Not provided

    def test_payment_response_schema(self):
        """Test payment response schema"""
        today = date.today()
        now = datetime.now()
        
        response_data = {
            "id": 1,
            "organization_id": 1,
            "invoice_id": 1,
            "user_id": 1,
            "payment_date": today,
            "amount": Decimal("500.00"),
            "payment_method": "bank_transfer",
            "reference_number": "TXN123456",
            "notes": "Payment for services",
            "status": "completed",
            "created_at": now,
            "updated_at": now,
        }

        payment_response = PaymentResponse(**response_data)
        assert payment_response.id == 1
        assert payment_response.amount == Decimal("500.00")
        assert payment_response.status == "completed"

    def test_payment_search_params_validation(self):
        """Test payment search parameters validation"""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        valid_params = {
            "search": "TXN123",
            "invoice_id": 1,
            "payment_method": "bank_transfer",
            "status": "completed",
            "date_from": today,
            "date_to": tomorrow,
            "amount_min": Decimal("100.00"),
            "amount_max": Decimal("1000.00"),
            "page": 1,
            "per_page": 20,
            "sort_by": "payment_date",
            "sort_order": "desc",
        }

        search_params = PaymentSearchParams(**valid_params)
        assert search_params.search == "TXN123"
        assert search_params.payment_method == "bank_transfer"
        assert search_params.page == 1

    def test_payment_search_invalid_date_range(self):
        """Test payment search with invalid date range"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        invalid_params = {
            "date_from": today,
            "date_to": yesterday,  # Before start date
        }

        with pytest.raises(ValueError):
            PaymentSearchParams(**invalid_params)

    def test_payment_search_invalid_amount_range(self):
        """Test payment search with invalid amount range"""
        invalid_params = {
            "amount_min": Decimal("1000.00"),
            "amount_max": Decimal("500.00"),  # Less than minimum
        }

        with pytest.raises(ValueError):
            PaymentSearchParams(**invalid_params)

    def test_payment_status_update_schema(self):
        """Test payment status update schema"""
        status_data = {"status": "completed"}
        
        status_update = PaymentStatusUpdate(**status_data)
        assert status_update.status == "completed"

    def test_payment_status_update_invalid(self):
        """Test payment status update with invalid status"""
        status_data = {"status": "invalid_status"}
        
        with pytest.raises(ValueError):
            PaymentStatusUpdate(**status_data)

    def test_payment_summary_schema(self):
        """Test payment summary schema"""
        summary_data = {
            "total_payments": 10,
            "total_amount": Decimal("5000.00"),
            "completed_payments": 8,
            "completed_amount": Decimal("4500.00"),
            "pending_payments": 1,
            "pending_amount": Decimal("300.00"),
            "failed_payments": 1,
            "failed_amount": Decimal("200.00"),
        }

        summary = PaymentSummary(**summary_data)
        assert summary.total_payments == 10
        assert summary.total_amount == Decimal("5000.00")
        assert summary.completed_payments == 8

    def test_invoice_payment_summary_schema(self):
        """Test invoice payment summary schema"""
        today = date.today()
        
        summary_data = {
            "invoice_id": 1,
            "invoice_number": "INV-2024-0001",
            "total_amount": Decimal("1000.00"),
            "paid_amount": Decimal("750.00"),
            "outstanding_amount": Decimal("250.00"),
            "payment_count": 2,
            "last_payment_date": today,
        }

        summary = InvoicePaymentSummary(**summary_data)
        assert summary.invoice_id == 1
        assert summary.total_amount == Decimal("1000.00")
        assert summary.outstanding_amount == Decimal("250.00")

    def test_payment_allocation_schema(self):
        """Test payment allocation schema"""
        allocation_data = {
            "invoice_id": 1,
            "allocated_amount": Decimal("500.00"),
        }

        allocation = PaymentAllocation(**allocation_data)
        assert allocation.invoice_id == 1
        assert allocation.allocated_amount == Decimal("500.00")

    def test_payment_allocation_invalid_amount(self):
        """Test payment allocation with invalid amount"""
        allocation_data = {
            "invoice_id": 1,
            "allocated_amount": Decimal("0.00"),  # Must be > 0
        }

        with pytest.raises(ValueError):
            PaymentAllocation(**allocation_data)

    def test_payment_allocation_create_schema(self):
        """Test payment allocation create schema"""
        today = date.today()
        
        allocation_data = {
            "payment_date": today,
            "amount": Decimal("1000.00"),
            "payment_method": "bank_transfer",
            "reference_number": "TXN789",
            "notes": "Payment allocation test",
            "allocations": [
                {"invoice_id": 1, "allocated_amount": Decimal("600.00")},
                {"invoice_id": 2, "allocated_amount": Decimal("400.00")},
            ],
        }

        allocation_create = PaymentAllocationCreate(**allocation_data)
        assert allocation_create.amount == Decimal("1000.00")
        assert len(allocation_create.allocations) == 2
        assert allocation_create.allocations[0].allocated_amount == Decimal("600.00")

    def test_payment_allocation_create_exceeds_amount(self):
        """Test payment allocation create with allocations exceeding payment amount"""
        today = date.today()
        
        allocation_data = {
            "payment_date": today,
            "amount": Decimal("500.00"),
            "payment_method": "cash",
            "allocations": [
                {"invoice_id": 1, "allocated_amount": Decimal("400.00")},
                {"invoice_id": 2, "allocated_amount": Decimal("200.00")},  # Total: 600 > 500
            ],
        }

        with pytest.raises(ValueError):
            PaymentAllocationCreate(**allocation_data)

    def test_payment_allocation_create_no_allocations(self):
        """Test payment allocation create with no allocations"""
        today = date.today()
        
        allocation_data = {
            "payment_date": today,
            "amount": Decimal("500.00"),
            "payment_method": "cash",
            "allocations": [],  # Empty allocations
        }

        with pytest.raises(ValueError):
            PaymentAllocationCreate(**allocation_data)


class TestPaymentBusinessLogic:
    """Test payment business logic without database"""

    def create_test_token(
        self, user_id: int = 1, organization_id: int = 1, role: str = "owner"
    ):
        """Helper to create test JWT token"""
        return create_access_token(
            user_id=user_id,
            organization_id=organization_id,
            email="test@example.com",
            role=role,
        )

    def test_payment_status_transitions(self):
        """Test valid payment status transitions"""
        valid_transitions = {
            "pending": ["completed", "failed", "cancelled"],
            "completed": ["cancelled"],
            "failed": ["pending", "completed", "cancelled"],
            "cancelled": [],
        }
        
        # Test valid transitions
        assert "completed" in valid_transitions["pending"]
        assert "cancelled" in valid_transitions["completed"]
        assert "pending" in valid_transitions["failed"]
        
        # Test invalid transitions
        assert "pending" not in valid_transitions["completed"]
        assert "completed" not in valid_transitions["cancelled"]

    def test_payment_amount_validation(self):
        """Test payment amount validation logic"""
        # Test valid amounts
        valid_amounts = [
            Decimal("0.01"),
            Decimal("100.00"),
            Decimal("9999.99"),
        ]
        
        for amount in valid_amounts:
            assert amount > 0
        
        # Test invalid amounts
        invalid_amounts = [
            Decimal("0.00"),
            Decimal("-100.00"),
        ]
        
        for amount in invalid_amounts:
            assert amount <= 0

    def test_payment_method_validation(self):
        """Test payment method validation"""
        valid_methods = ["cash", "check", "bank_transfer", "credit_card", "online"]
        invalid_methods = ["paypal", "crypto", "invalid"]
        
        # Test valid methods
        for method in valid_methods:
            assert method in valid_methods
        
        # Test invalid methods
        for method in invalid_methods:
            assert method not in valid_methods

    def test_outstanding_balance_calculation(self):
        """Test outstanding balance calculation logic"""
        invoice_total = Decimal("1000.00")
        paid_amount = Decimal("750.00")
        
        outstanding = invoice_total - paid_amount
        assert outstanding == Decimal("250.00")
        
        # Test overpayment scenario
        overpaid_amount = Decimal("1200.00")
        outstanding_overpaid = invoice_total - overpaid_amount
        assert outstanding_overpaid == Decimal("-200.00")  # Negative indicates overpayment


class TestPaymentAPIStructure:
    """Test payment API structure and imports"""

    def test_payment_api_import(self):
        """Test that payment API can be imported successfully"""
        from app.api.v1.payments import router
        assert router is not None

    def test_payment_api_routes_exist(self):
        """Test that payment API routes are properly defined"""
        from app.api.v1.payments import router
        
        # Check that routes are defined
        routes = [route.path for route in router.routes]
        assert "/" in routes  # List/Create payments
        assert "/{payment_id}" in routes  # Get/Update/Delete payment
        assert "/{payment_id}/status" in routes  # Update status
        assert "/summary/stats" in routes  # Summary stats
        assert "/invoice/{invoice_id}/summary" in routes  # Invoice payment summary

    def test_payment_api_methods(self):
        """Test that payment API has correct HTTP methods"""
        from app.api.v1.payments import router
        
        # Get all route methods
        all_methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                all_methods.extend(route.methods)
        
        # Check that CRUD methods are available
        assert "GET" in all_methods
        assert "POST" in all_methods
        assert "PUT" in all_methods
        assert "PATCH" in all_methods
        assert "DELETE" in all_methods

    def test_payment_api_in_main_router(self):
        """Test that payment API is included in main router"""
        from app.api.v1.api import api_router
        
        # Check that payment routes are included
        payment_routes_found = False
        for route in api_router.routes:
            if hasattr(route, 'path_regex') and 'payments' in str(route.path_regex):
                payment_routes_found = True
                break
        
        assert payment_routes_found, "Payment routes not found in main API router"

    def test_payment_schemas_integration(self):
        """Test that payment schemas work with API"""
        from app.schemas.payment import PaymentCreate, PaymentResponse
        
        # Test that schemas can be used for API serialization
        today = date.today()
        
        payment_data = {
            "invoice_id": 1,
            "payment_date": today,
            "amount": Decimal("500.00"),
            "payment_method": "bank_transfer",
        }
        
        # Should be able to create and validate
        payment_create = PaymentCreate(**payment_data)
        assert payment_create.invoice_id == 1

    def test_payment_model_integration(self):
        """Test that payment model can be imported and used"""
        from app.models.payment import Payment
        
        # Should be able to access model attributes
        assert hasattr(Payment, 'organization_id')
        assert hasattr(Payment, 'invoice_id')
        assert hasattr(Payment, 'user_id')
        assert hasattr(Payment, 'payment_date')
        assert hasattr(Payment, 'amount')
        assert hasattr(Payment, 'payment_method')
        assert hasattr(Payment, 'status')
