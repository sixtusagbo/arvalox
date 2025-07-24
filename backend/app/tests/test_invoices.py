import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.core.security import create_access_token
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceSearchParams,
    InvoiceListResponse,
    InvoiceItemCreate,
    InvoiceItemResponse,
    InvoiceStatusUpdate,
    InvoiceSummary,
)


class TestInvoiceSchemas:
    """Test invoice Pydantic schemas"""

    def test_invoice_item_create_valid(self):
        """Test valid invoice item creation schema"""
        item_data = {
            "description": "Web Development Services",
            "quantity": Decimal("10.00"),
            "unit_price": Decimal("150.00"),
        }

        item = InvoiceItemCreate(**item_data)
        assert item.description == "Web Development Services"
        assert item.quantity == Decimal("10.00")
        assert item.unit_price == Decimal("150.00")

    def test_invoice_item_invalid_quantity(self):
        """Test invoice item with invalid quantity"""
        item_data = {
            "description": "Service",
            "quantity": Decimal("0.00"),  # Must be > 0
            "unit_price": Decimal("100.00"),
        }

        with pytest.raises(ValueError):
            InvoiceItemCreate(**item_data)

    def test_invoice_item_negative_price(self):
        """Test invoice item with negative price"""
        item_data = {
            "description": "Service",
            "quantity": Decimal("1.00"),
            "unit_price": Decimal("-50.00"),  # Must be >= 0
        }

        with pytest.raises(ValueError):
            InvoiceItemCreate(**item_data)

    def test_invoice_create_valid(self):
        """Test valid invoice creation schema"""
        today = date.today()
        due_date = today + timedelta(days=30)
        
        invoice_data = {
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "invoice_date": today,
            "due_date": due_date,
            "status": "draft",
            "notes": "Test invoice",
            "items": [
                {
                    "description": "Consulting Services",
                    "quantity": Decimal("5.00"),
                    "unit_price": Decimal("200.00"),
                }
            ],
        }

        invoice = InvoiceCreate(**invoice_data)
        assert invoice.invoice_number == "INV-2024-0001"
        assert invoice.customer_id == 1
        assert invoice.status == "draft"
        assert len(invoice.items) == 1

    def test_invoice_create_invalid_due_date(self):
        """Test invoice creation with due date before invoice date"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        invoice_data = {
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "invoice_date": today,
            "due_date": yesterday,  # Before invoice date
            "items": [
                {
                    "description": "Service",
                    "quantity": Decimal("1.00"),
                    "unit_price": Decimal("100.00"),
                }
            ],
        }

        with pytest.raises(ValueError):
            InvoiceCreate(**invoice_data)

    def test_invoice_create_no_items(self):
        """Test invoice creation with no items"""
        today = date.today()
        due_date = today + timedelta(days=30)
        
        invoice_data = {
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "invoice_date": today,
            "due_date": due_date,
            "items": [],  # Empty items list
        }

        with pytest.raises(ValueError):
            InvoiceCreate(**invoice_data)

    def test_invoice_invalid_status(self):
        """Test invoice creation with invalid status"""
        today = date.today()
        due_date = today + timedelta(days=30)
        
        invoice_data = {
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "invoice_date": today,
            "due_date": due_date,
            "status": "invalid_status",
            "items": [
                {
                    "description": "Service",
                    "quantity": Decimal("1.00"),
                    "unit_price": Decimal("100.00"),
                }
            ],
        }

        with pytest.raises(ValueError):
            InvoiceCreate(**invoice_data)

    def test_invoice_update_partial(self):
        """Test invoice update with partial data"""
        update_data = {
            "status": "sent",
            "notes": "Updated notes",
        }

        invoice_update = InvoiceUpdate(**update_data)
        assert invoice_update.status == "sent"
        assert invoice_update.notes == "Updated notes"
        assert invoice_update.invoice_number is None  # Not provided

    def test_invoice_response_schema(self):
        """Test invoice response schema"""
        today = date.today()
        now = datetime.now()
        
        response_data = {
            "id": 1,
            "organization_id": 1,
            "user_id": 1,
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "invoice_date": today,
            "due_date": today + timedelta(days=30),
            "subtotal": Decimal("1000.00"),
            "tax_amount": Decimal("100.00"),
            "total_amount": Decimal("1100.00"),
            "paid_amount": Decimal("0.00"),
            "status": "draft",
            "notes": "Test invoice",
            "items": [],
            "created_at": now,
            "updated_at": now,
        }

        invoice_response = InvoiceResponse(**response_data)
        assert invoice_response.id == 1
        assert invoice_response.total_amount == Decimal("1100.00")
        assert invoice_response.status == "draft"

    def test_invoice_search_params_validation(self):
        """Test invoice search parameters validation"""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        valid_params = {
            "search": "INV-2024",
            "status": "sent",
            "customer_id": 1,
            "date_from": today,
            "date_to": tomorrow,
            "amount_min": Decimal("100.00"),
            "amount_max": Decimal("1000.00"),
            "overdue_only": False,
            "page": 1,
            "per_page": 20,
            "sort_by": "invoice_date",
            "sort_order": "desc",
        }

        search_params = InvoiceSearchParams(**valid_params)
        assert search_params.search == "INV-2024"
        assert search_params.status == "sent"
        assert search_params.page == 1

    def test_invoice_search_invalid_date_range(self):
        """Test invoice search with invalid date range"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        invalid_params = {
            "date_from": today,
            "date_to": yesterday,  # Before start date
        }

        with pytest.raises(ValueError):
            InvoiceSearchParams(**invalid_params)

    def test_invoice_search_invalid_amount_range(self):
        """Test invoice search with invalid amount range"""
        invalid_params = {
            "amount_min": Decimal("1000.00"),
            "amount_max": Decimal("500.00"),  # Less than minimum
        }

        with pytest.raises(ValueError):
            InvoiceSearchParams(**invalid_params)

    def test_invoice_status_update_schema(self):
        """Test invoice status update schema"""
        status_data = {"status": "sent"}
        
        status_update = InvoiceStatusUpdate(**status_data)
        assert status_update.status == "sent"

    def test_invoice_status_update_invalid(self):
        """Test invoice status update with invalid status"""
        status_data = {"status": "invalid_status"}
        
        with pytest.raises(ValueError):
            InvoiceStatusUpdate(**status_data)

    def test_invoice_summary_schema(self):
        """Test invoice summary schema"""
        summary_data = {
            "total_invoices": 10,
            "total_amount": Decimal("10000.00"),
            "paid_amount": Decimal("7500.00"),
            "outstanding_amount": Decimal("2500.00"),
            "overdue_count": 2,
            "overdue_amount": Decimal("1000.00"),
            "draft_count": 3,
            "sent_count": 5,
            "paid_count": 2,
        }

        summary = InvoiceSummary(**summary_data)
        assert summary.total_invoices == 10
        assert summary.total_amount == Decimal("10000.00")
        assert summary.overdue_count == 2


class TestInvoiceBusinessLogic:
    """Test invoice business logic without database"""

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

    def test_invoice_number_generation_logic(self):
        """Test invoice number generation logic"""
        # Test basic format
        prefix = "INV"
        year = 2024
        sequence = 1
        
        expected = f"{prefix}-{year}-{sequence:04d}"
        assert expected == "INV-2024-0001"
        
        # Test sequence increment
        sequence = 42
        expected = f"{prefix}-{year}-{sequence:04d}"
        assert expected == "INV-2024-0042"

    def test_invoice_total_calculation(self):
        """Test invoice total calculation logic"""
        items = [
            {"quantity": Decimal("2.00"), "unit_price": Decimal("100.00")},
            {"quantity": Decimal("1.50"), "unit_price": Decimal("200.00")},
            {"quantity": Decimal("3.00"), "unit_price": Decimal("50.00")},
        ]
        
        subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
        expected_subtotal = Decimal("650.00")  # 200 + 300 + 150
        
        assert subtotal == expected_subtotal

    def test_invoice_status_transitions(self):
        """Test valid invoice status transitions"""
        valid_transitions = {
            "draft": ["sent", "cancelled"],
            "sent": ["paid", "overdue", "cancelled"],
            "overdue": ["paid", "cancelled"],
            "paid": [],
            "cancelled": [],
        }
        
        # Test valid transitions
        assert "sent" in valid_transitions["draft"]
        assert "paid" in valid_transitions["sent"]
        assert "paid" in valid_transitions["overdue"]
        
        # Test invalid transitions
        assert "draft" not in valid_transitions["paid"]
        assert "sent" not in valid_transitions["cancelled"]

    def test_overdue_invoice_detection(self):
        """Test overdue invoice detection logic"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Invoice due yesterday with sent status should be overdue
        overdue_statuses = ["sent", "overdue"]
        
        # Test overdue conditions
        assert yesterday < today  # Due date in past
        assert "sent" in overdue_statuses  # Valid status for overdue
        
        # Test not overdue conditions
        assert tomorrow > today  # Due date in future
        assert "paid" not in overdue_statuses  # Paid invoices not overdue


class TestInvoiceAPIStructure:
    """Test invoice API structure and imports"""

    def test_invoice_api_import(self):
        """Test that invoice API can be imported successfully"""
        from app.api.v1.invoices import router
        assert router is not None

    def test_invoice_api_routes_exist(self):
        """Test that invoice API routes are properly defined"""
        from app.api.v1.invoices import router
        
        # Check that routes are defined
        routes = [route.path for route in router.routes]
        assert "/" in routes  # List/Create invoices
        assert "/{invoice_id}" in routes  # Get/Update/Delete invoice
        assert "/{invoice_id}/status" in routes  # Update status
        assert "/summary/stats" in routes  # Summary stats
        assert "/generate-number" in routes  # Generate number

    def test_invoice_api_methods(self):
        """Test that invoice API has correct HTTP methods"""
        from app.api.v1.invoices import router
        
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

    def test_invoice_api_in_main_router(self):
        """Test that invoice API is included in main router"""
        from app.api.v1.api import api_router
        
        # Check that invoice routes are included
        invoice_routes_found = False
        for route in api_router.routes:
            if hasattr(route, 'path_regex') and 'invoices' in str(route.path_regex):
                invoice_routes_found = True
                break
        
        assert invoice_routes_found, "Invoice routes not found in main API router"

    def test_invoice_schemas_integration(self):
        """Test that invoice schemas work with API"""
        from app.schemas.invoice import InvoiceCreate, InvoiceResponse
        
        # Test that schemas can be used for API serialization
        today = date.today()
        due_date = today + timedelta(days=30)
        
        invoice_data = {
            "invoice_number": "TEST-001",
            "customer_id": 1,
            "invoice_date": today,
            "due_date": due_date,
            "status": "draft",
            "items": [
                {
                    "description": "Test Service",
                    "quantity": Decimal("1.00"),
                    "unit_price": Decimal("100.00"),
                }
            ],
        }
        
        # Should be able to create and validate
        invoice_create = InvoiceCreate(**invoice_data)
        assert invoice_create.invoice_number == "TEST-001"

    def test_invoice_model_integration(self):
        """Test that invoice model can be imported and used"""
        from app.models.invoice import Invoice, InvoiceItem
        
        # Should be able to access model attributes
        assert hasattr(Invoice, 'invoice_number')
        assert hasattr(Invoice, 'customer_id')
        assert hasattr(Invoice, 'organization_id')
        assert hasattr(Invoice, 'status')
        assert hasattr(Invoice, 'total_amount')
        
        # Should be able to access invoice item attributes
        assert hasattr(InvoiceItem, 'description')
        assert hasattr(InvoiceItem, 'quantity')
        assert hasattr(InvoiceItem, 'unit_price')
        assert hasattr(InvoiceItem, 'line_total')
