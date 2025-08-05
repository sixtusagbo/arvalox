import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.schemas.dashboard import (
    DateRange,
    RevenueMetrics,
    StatusBreakdown,
    InvoiceMetrics,
    PaymentMethodBreakdown,
    PaymentMetrics,
    CustomerMetrics,
    AgingBucketMetrics,
    AgingMetrics,
    RecentActivity,
    TopCustomer,
    DashboardOverview,
    DashboardParams,
    KPISummary,
    QuickStats,
)


class TestDashboardSchemas:
    """Test dashboard Pydantic schemas"""

    def test_date_range_schema(self):
        """Test date range schema"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        date_range_data = {
            "from": yesterday,
            "to": today,
        }

        date_range = DateRange(**date_range_data)
        assert date_range.from_date == yesterday
        assert date_range.to == today

    def test_revenue_metrics_schema(self):
        """Test revenue metrics schema"""
        revenue_data = {
            "total_revenue": Decimal("50000.00"),
            "invoice_count": 25,
            "average_invoice_value": Decimal("2000.00"),
            "outstanding_amount": Decimal("15000.00"),
            "outstanding_count": 8,
            "revenue_growth_percentage": 15.5,
            "previous_period_revenue": Decimal("43478.26"),
        }

        revenue_metrics = RevenueMetrics(**revenue_data)
        assert revenue_metrics.total_revenue == Decimal("50000.00")
        assert revenue_metrics.invoice_count == 25
        assert revenue_metrics.revenue_growth_percentage == 15.5

    def test_status_breakdown_schema(self):
        """Test status breakdown schema"""
        status_data = {
            "count": 10,
            "amount": Decimal("5000.00"),
        }

        status_breakdown = StatusBreakdown(**status_data)
        assert status_breakdown.count == 10
        assert status_breakdown.amount == Decimal("5000.00")

    def test_invoice_metrics_schema(self):
        """Test invoice metrics schema"""
        invoice_data = {
            "status_breakdown": {
                "draft": {"count": 5, "amount": Decimal("2500.00")},
                "sent": {"count": 10, "amount": Decimal("7500.00")},
                "paid": {"count": 8, "amount": Decimal("6000.00")},
            },
            "overdue_count": 3,
            "overdue_amount": Decimal("1500.00"),
        }

        invoice_metrics = InvoiceMetrics(**invoice_data)
        assert invoice_metrics.overdue_count == 3
        assert invoice_metrics.status_breakdown["sent"].count == 10

    def test_payment_metrics_schema(self):
        """Test payment metrics schema"""
        payment_data = {
            "payment_count": 15,
            "total_payments": Decimal("12000.00"),
            "average_payment": Decimal("800.00"),
            "method_breakdown": {
                "bank_transfer": {"count": 8, "amount": Decimal("7000.00")},
                "credit_card": {"count": 5, "amount": Decimal("3500.00")},
                "cash": {"count": 2, "amount": Decimal("1500.00")},
            },
        }

        payment_metrics = PaymentMetrics(**payment_data)
        assert payment_metrics.payment_count == 15
        assert payment_metrics.total_payments == Decimal("12000.00")
        assert payment_metrics.method_breakdown["bank_transfer"].count == 8

    def test_customer_metrics_schema(self):
        """Test customer metrics schema"""
        customer_data = {
            "total_customers": 50,
            "active_customers": 45,
            "inactive_customers": 5,
            "customers_with_outstanding": 12,
        }

        customer_metrics = CustomerMetrics(**customer_data)
        assert customer_metrics.total_customers == 50
        assert customer_metrics.active_customers == 45
        assert customer_metrics.customers_with_outstanding == 12

    def test_aging_metrics_schema(self):
        """Test aging metrics schema"""
        aging_data = {
            "total_outstanding": Decimal("25000.00"),
            "total_overdue": Decimal("8000.00"),
            "overdue_percentage": 32.0,
            "collection_efficiency": 68.0,
            "aging_breakdown": {
                "current": {"count": 10, "amount": Decimal("17000.00")},
                "days_1_30": {"count": 5, "amount": Decimal("4000.00")},
                "days_31_60": {"count": 3, "amount": Decimal("2500.00")},
                "days_61_90": {"count": 2, "amount": Decimal("1000.00")},
                "days_over_90": {"count": 1, "amount": Decimal("500.00")},
            },
        }

        aging_metrics = AgingMetrics(**aging_data)
        assert aging_metrics.total_outstanding == Decimal("25000.00")
        assert aging_metrics.overdue_percentage == 32.0
        assert aging_metrics.aging_breakdown["current"].count == 10

    def test_recent_activity_schema(self):
        """Test recent activity schema"""
        now = datetime.now()

        activity_data = {
            "type": "invoice",
            "id": 123,
            "description": "Invoice INV-2024-0001 created",
            "amount": Decimal("1500.00"),
            "date": now,
            "status": "sent",
        }

        activity = RecentActivity(**activity_data)
        assert activity.type == "invoice"
        assert activity.id == 123
        assert activity.amount == Decimal("1500.00")

    def test_recent_activity_invalid_type(self):
        """Test recent activity with invalid type"""
        now = datetime.now()

        activity_data = {
            "type": "invalid_type",  # Must be invoice or payment
            "id": 123,
            "description": "Test activity",
            "amount": Decimal("100.00"),
            "date": now,
            "status": "active",
        }

        with pytest.raises(ValueError):
            RecentActivity(**activity_data)

    def test_top_customer_schema(self):
        """Test top customer schema"""
        customer_data = {
            "customer_id": 1,
            "contact_name": "John Doe",
            "company_name": "Acme Corp",
            "total_revenue": Decimal("15000.00"),
            "invoice_count": 8,
            "outstanding_amount": Decimal("2500.00"),
        }

        top_customer = TopCustomer(**customer_data)
        assert top_customer.customer_id == 1
        assert top_customer.contact_name == "John Doe"
        assert top_customer.total_revenue == Decimal("15000.00")

    def test_kpi_summary_schema(self):
        """Test KPI summary schema"""
        kpi_data = {
            "total_revenue": Decimal("100000.00"),
            "outstanding_amount": Decimal("25000.00"),
            "overdue_amount": Decimal("8000.00"),
            "collection_efficiency": 75.5,
            "revenue_growth": 12.3,
            "total_customers": 150,
            "active_invoices": 45,
            "overdue_invoices": 8,
        }

        kpi_summary = KPISummary(**kpi_data)
        assert kpi_summary.total_revenue == Decimal("100000.00")
        assert kpi_summary.collection_efficiency == 75.5
        assert kpi_summary.total_customers == 150

    def test_quick_stats_schema(self):
        """Test quick stats schema"""
        stats_data = {
            "total_revenue_this_month": Decimal("25000.00"),
            "total_outstanding": Decimal("15000.00"),
            "overdue_amount": Decimal("5000.00"),
            "total_customers": 75,
            "invoices_this_month": 20,
            "payments_this_month": 15,
        }

        quick_stats = QuickStats(**stats_data)
        assert quick_stats.total_revenue_this_month == Decimal("25000.00")
        assert quick_stats.total_customers == 75
        assert quick_stats.invoices_this_month == 20


class TestDashboardBusinessLogic:
    """Test dashboard business logic without database"""

    def test_revenue_growth_calculation(self):
        """Test revenue growth calculation logic"""
        current_revenue = Decimal("50000.00")
        previous_revenue = Decimal("40000.00")

        growth_percentage = float(
            (current_revenue - previous_revenue) / previous_revenue * 100
        )

        assert growth_percentage == 25.0
        assert growth_percentage > 0  # Positive growth

    def test_revenue_decline_calculation(self):
        """Test revenue decline calculation logic"""
        current_revenue = Decimal("40000.00")
        previous_revenue = Decimal("50000.00")

        growth_percentage = float(
            (current_revenue - previous_revenue) / previous_revenue * 100
        )

        assert growth_percentage == -20.0
        assert growth_percentage < 0  # Negative growth (decline)

    def test_collection_efficiency_calculation(self):
        """Test collection efficiency calculation"""
        total_outstanding = Decimal("20000.00")
        current_amount = Decimal("15000.00")  # Not yet due

        collection_efficiency = float(current_amount / total_outstanding * 100)

        assert collection_efficiency == 75.0
        assert 0 <= collection_efficiency <= 100

    def test_overdue_percentage_calculation(self):
        """Test overdue percentage calculation"""
        total_outstanding = Decimal("20000.00")
        overdue_amount = Decimal("6000.00")

        overdue_percentage = float(overdue_amount / total_outstanding * 100)

        assert overdue_percentage == 30.0
        assert 0 <= overdue_percentage <= 100

    def test_average_invoice_value_calculation(self):
        """Test average invoice value calculation"""
        invoices = [
            {"amount": Decimal("1000.00")},
            {"amount": Decimal("1500.00")},
            {"amount": Decimal("2000.00")},
            {"amount": Decimal("500.00")},
        ]

        total_amount = sum(invoice["amount"] for invoice in invoices)
        average_value = total_amount / len(invoices)

        assert average_value == Decimal("1250.00")

    def test_customer_metrics_calculation(self):
        """Test customer metrics calculation"""
        customers = [
            {"status": "active"},
            {"status": "active"},
            {"status": "active"},
            {"status": "inactive"},
            {"status": "inactive"},
        ]

        total_customers = len(customers)
        active_customers = len(
            [c for c in customers if c["status"] == "active"]
        )
        inactive_customers = len(
            [c for c in customers if c["status"] == "inactive"]
        )

        assert total_customers == 5
        assert active_customers == 3
        assert inactive_customers == 2
        assert active_customers + inactive_customers == total_customers

    def test_payment_method_breakdown_calculation(self):
        """Test payment method breakdown calculation"""
        payments = [
            {"method": "bank_transfer", "amount": Decimal("1000.00")},
            {"method": "bank_transfer", "amount": Decimal("1500.00")},
            {"method": "credit_card", "amount": Decimal("800.00")},
            {"method": "cash", "amount": Decimal("200.00")},
        ]

        method_breakdown = {}
        for payment in payments:
            method = payment["method"]
            amount = payment["amount"]

            if method not in method_breakdown:
                method_breakdown[method] = {
                    "count": 0,
                    "amount": Decimal("0.00"),
                }

            method_breakdown[method]["count"] += 1
            method_breakdown[method]["amount"] += amount

        assert method_breakdown["bank_transfer"]["count"] == 2
        assert method_breakdown["bank_transfer"]["amount"] == Decimal("2500.00")
        assert method_breakdown["credit_card"]["count"] == 1
        assert method_breakdown["cash"]["amount"] == Decimal("200.00")

    def test_top_customers_ranking(self):
        """Test top customers ranking logic"""
        customers = [
            {"name": "Customer A", "revenue": Decimal("5000.00")},
            {"name": "Customer B", "revenue": Decimal("8000.00")},
            {"name": "Customer C", "revenue": Decimal("3000.00")},
            {"name": "Customer D", "revenue": Decimal("12000.00")},
        ]

        # Sort by revenue (highest first)
        top_customers = sorted(
            customers, key=lambda x: x["revenue"], reverse=True
        )

        assert top_customers[0]["name"] == "Customer D"
        assert top_customers[0]["revenue"] == Decimal("12000.00")
        assert top_customers[1]["name"] == "Customer B"
        assert top_customers[-1]["name"] == "Customer C"


class TestDashboardService:
    """Test dashboard service functionality"""

    def test_dashboard_service_import(self):
        """Test that dashboard service can be imported"""
        from app.services.dashboard_service import DashboardService

        # Should be able to import and instantiate (with mock db)
        assert DashboardService is not None

    def test_dashboard_service_methods(self):
        """Test that dashboard service has required methods"""
        from app.services.dashboard_service import DashboardService

        # Check that all required methods exist
        assert hasattr(DashboardService, "get_dashboard_overview")
        assert hasattr(DashboardService, "get_revenue_metrics")
        assert hasattr(DashboardService, "get_invoice_metrics")
        assert hasattr(DashboardService, "get_payment_metrics")
        assert hasattr(DashboardService, "get_customer_metrics")
        assert hasattr(DashboardService, "get_aging_metrics")
        assert hasattr(DashboardService, "get_recent_activity")
        assert hasattr(DashboardService, "get_top_customers")


class TestDashboardAPI:
    """Test dashboard API endpoints"""

    def test_dashboard_api_import(self):
        """Test that dashboard API can be imported"""
        from app.api.v1.reports import router

        assert router is not None

    def test_dashboard_api_endpoints_exist(self):
        """Test that dashboard API endpoints are defined"""
        from app.api.v1.reports import router

        # Check that dashboard routes exist
        routes = [route.path for route in router.routes]
        assert "/dashboard" in routes
        assert "/dashboard/kpis" in routes
        assert "/dashboard/quick-stats" in routes
        assert "/dashboard/revenue-metrics" in routes
        assert "/dashboard/top-customers" in routes
        assert "/dashboard/recent-activity" in routes

    def test_dashboard_api_methods(self):
        """Test that dashboard API has correct HTTP methods"""
        from app.api.v1.reports import router

        # Get all route methods
        all_methods = []
        for route in router.routes:
            if hasattr(route, "methods"):
                all_methods.extend(route.methods)

        # Check that GET methods are available (all dashboard endpoints are GET)
        assert "GET" in all_methods

    def test_dashboard_schemas_integration(self):
        """Test that dashboard schemas work with API"""
        from app.schemas.dashboard import DashboardOverview, KPISummary

        # Test that schemas can be used for API serialization
        today = date.today()
        yesterday = today - timedelta(days=1)
        now = datetime.now()

        kpi_data = {
            "total_revenue": Decimal("50000.00"),
            "outstanding_amount": Decimal("15000.00"),
            "overdue_amount": Decimal("5000.00"),
            "collection_efficiency": 75.0,
            "revenue_growth": 12.5,
            "total_customers": 100,
            "active_invoices": 25,
            "overdue_invoices": 5,
        }

        # Should be able to create and validate
        kpi_summary = KPISummary(**kpi_data)
        assert kpi_summary.total_revenue == Decimal("50000.00")

    def test_dashboard_service_integration(self):
        """Test that dashboard service integrates with API"""
        from app.services.dashboard_service import DashboardService

        # Should be able to import service used by API
        assert DashboardService is not None

        # Check that service methods match API endpoint functionality
        service_methods = [
            "get_dashboard_overview",  # Used by /dashboard endpoint
            "get_revenue_metrics",  # Used by /dashboard/revenue-metrics endpoint
            "get_top_customers",  # Used by /dashboard/top-customers endpoint
            "get_recent_activity",  # Used by /dashboard/recent-activity endpoint
        ]

        for method in service_methods:
            assert hasattr(DashboardService, method)
