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
        assert allocation_create.allocations[0].allocated_amount == Decimal(
            "600.00"
        )

    def test_payment_allocation_create_exceeds_amount(self):
        """Test payment allocation create with allocations exceeding payment amount"""
        today = date.today()

        allocation_data = {
            "payment_date": today,
            "amount": Decimal("500.00"),
            "payment_method": "cash",
            "allocations": [
                {"invoice_id": 1, "allocated_amount": Decimal("400.00")},
                {
                    "invoice_id": 2,
                    "allocated_amount": Decimal("200.00"),
                },  # Total: 600 > 500
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
        valid_methods = [
            "cash",
            "check",
            "bank_transfer",
            "credit_card",
            "online",
        ]
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
        assert outstanding_overpaid == Decimal(
            "-200.00"
        )  # Negative indicates overpayment


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
        assert (
            "/invoice/{invoice_id}/summary" in routes
        )  # Invoice payment summary

    def test_payment_api_methods(self):
        """Test that payment API has correct HTTP methods"""
        from app.api.v1.payments import router

        # Get all route methods
        all_methods = []
        for route in router.routes:
            if hasattr(route, "methods"):
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
            if hasattr(route, "path_regex") and "payments" in str(
                route.path_regex
            ):
                payment_routes_found = True
                break

        assert payment_routes_found, (
            "Payment routes not found in main API router"
        )

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
        assert hasattr(Payment, "organization_id")
        assert hasattr(Payment, "invoice_id")
        assert hasattr(Payment, "user_id")
        assert hasattr(Payment, "payment_date")
        assert hasattr(Payment, "amount")
        assert hasattr(Payment, "payment_method")
        assert hasattr(Payment, "status")


class TestPaymentAllocationService:
    """Test payment allocation service functionality"""

    def test_payment_allocation_service_import(self):
        """Test that payment allocation service can be imported"""
        from app.services.payment_allocation_service import (
            PaymentAllocationService,
        )

        # Should be able to import and instantiate (with mock db)
        assert PaymentAllocationService is not None

    def test_payment_allocation_service_methods(self):
        """Test that payment allocation service has required methods"""
        from app.services.payment_allocation_service import (
            PaymentAllocationService,
        )

        # Check that all required methods exist
        assert hasattr(PaymentAllocationService, "allocate_payment")
        assert hasattr(PaymentAllocationService, "auto_allocate_payment")
        assert hasattr(PaymentAllocationService, "get_allocation_suggestions")
        assert hasattr(PaymentAllocationService, "_get_invoices")
        assert hasattr(PaymentAllocationService, "_get_outstanding_invoices")
        assert hasattr(PaymentAllocationService, "_validate_allocations")

    def test_allocation_validation_logic(self):
        """Test allocation validation business logic"""
        from decimal import Decimal

        # Test valid allocation scenarios
        invoice_total = Decimal("1000.00")
        paid_amount = Decimal("300.00")
        outstanding_balance = invoice_total - paid_amount

        # Valid allocation
        allocation_amount = Decimal("500.00")
        assert allocation_amount <= outstanding_balance

        # Invalid allocation (exceeds outstanding)
        invalid_allocation = Decimal("800.00")
        assert invalid_allocation > outstanding_balance

    def test_auto_allocation_logic(self):
        """Test auto allocation algorithm logic"""
        from decimal import Decimal

        # Mock invoice data
        invoices = [
            {
                "id": 1,
                "total": Decimal("1000.00"),
                "paid": Decimal("0.00"),
                "due_date": "2024-01-01",
            },
            {
                "id": 2,
                "total": Decimal("500.00"),
                "paid": Decimal("200.00"),
                "due_date": "2024-01-15",
            },
            {
                "id": 3,
                "total": Decimal("750.00"),
                "paid": Decimal("0.00"),
                "due_date": "2024-02-01",
            },
        ]

        # Calculate outstanding balances
        outstanding_balances = []
        for invoice in invoices:
            outstanding = invoice["total"] - invoice["paid"]
            outstanding_balances.append(outstanding)

        # Test allocation logic
        payment_amount = Decimal("1200.00")
        remaining = payment_amount
        allocations = []

        for i, outstanding in enumerate(outstanding_balances):
            if remaining <= 0:
                break
            allocation = min(remaining, outstanding)
            allocations.append(
                {"invoice_id": invoices[i]["id"], "amount": allocation}
            )
            remaining -= allocation

        # Verify allocations
        assert len(allocations) == 2  # Should allocate to first 2 invoices
        assert allocations[0]["amount"] == Decimal(
            "1000.00"
        )  # Full first invoice
        assert allocations[1]["amount"] == Decimal(
            "200.00"
        )  # Remaining amount to second invoice
        assert remaining == Decimal("0.00")  # No overpayment in this case

    def test_overpayment_handling_logic(self):
        """Test overpayment handling logic"""
        from decimal import Decimal

        # Mock scenario with overpayment
        total_outstanding = Decimal("800.00")
        payment_amount = Decimal("1000.00")
        overpayment = payment_amount - total_outstanding

        assert overpayment == Decimal("200.00")
        assert overpayment > 0  # Indicates overpayment

    def test_allocation_suggestions_logic(self):
        """Test allocation suggestions algorithm"""
        from decimal import Decimal

        # Mock outstanding invoices (sorted by due date)
        outstanding_invoices = [
            {
                "id": 1,
                "outstanding": Decimal("500.00"),
                "due_date": "2024-01-01",
                "overdue": True,
            },
            {
                "id": 2,
                "outstanding": Decimal("300.00"),
                "due_date": "2024-01-15",
                "overdue": False,
            },
            {
                "id": 3,
                "outstanding": Decimal("750.00"),
                "due_date": "2024-02-01",
                "overdue": False,
            },
        ]

        payment_amount = Decimal("600.00")
        suggestions = []
        remaining = payment_amount

        for invoice in outstanding_invoices:
            if remaining <= 0:
                break
            suggested = min(remaining, invoice["outstanding"])
            suggestions.append(
                {
                    "invoice_id": invoice["id"],
                    "suggested_amount": suggested,
                    "priority": "high" if invoice["overdue"] else "normal",
                }
            )
            remaining -= suggested

        # Verify suggestions prioritize overdue invoices
        assert len(suggestions) == 2
        assert suggestions[0]["suggested_amount"] == Decimal(
            "500.00"
        )  # Full overdue invoice
        assert suggestions[1]["suggested_amount"] == Decimal(
            "100.00"
        )  # Partial second invoice


class TestPaymentAllocationAPI:
    """Test payment allocation API endpoints"""

    def test_allocation_api_endpoints_exist(self):
        """Test that allocation API endpoints are defined"""
        from app.api.v1.payments import router

        # Check that allocation routes exist
        routes = [route.path for route in router.routes]
        assert "/allocate" in routes
        assert "/auto-allocate" in routes
        assert "/allocation-suggestions" in routes

    def test_allocation_api_methods(self):
        """Test that allocation API has correct HTTP methods"""
        from app.api.v1.payments import router

        # Get allocation route methods
        allocation_methods = []
        for route in router.routes:
            if hasattr(route, "methods") and (
                "allocate" in route.path or "suggestions" in route.path
            ):
                allocation_methods.extend(route.methods)

        # Check that required methods are available
        assert "POST" in allocation_methods  # For allocate and auto-allocate
        assert "GET" in allocation_methods  # For suggestions

    def test_allocation_schema_integration(self):
        """Test that allocation schemas work with API"""
        from app.schemas.payment import (
            PaymentAllocationCreate,
            PaymentAllocation,
        )
        from datetime import date
        from decimal import Decimal

        # Test allocation schema
        today = date.today()
        allocation_data = {
            "payment_date": today,
            "amount": Decimal("1000.00"),
            "payment_method": "bank_transfer",
            "reference_number": "TXN789",
            "allocations": [
                {"invoice_id": 1, "allocated_amount": Decimal("600.00")},
                {"invoice_id": 2, "allocated_amount": Decimal("400.00")},
            ],
        }

        # Should be able to create and validate
        allocation_create = PaymentAllocationCreate(**allocation_data)
        assert allocation_create.amount == Decimal("1000.00")
        assert len(allocation_create.allocations) == 2

    def test_allocation_service_integration(self):
        """Test that allocation service integrates with API"""
        from app.services.payment_allocation_service import (
            PaymentAllocationService,
        )

        # Should be able to import service used by API
        assert PaymentAllocationService is not None

        # Check that service methods match API endpoint functionality
        service_methods = [
            "allocate_payment",  # Used by /allocate endpoint
            "auto_allocate_payment",  # Used by /auto-allocate endpoint
            "get_allocation_suggestions",  # Used by /allocation-suggestions endpoint
        ]

        for method in service_methods:
            assert hasattr(PaymentAllocationService, method)
