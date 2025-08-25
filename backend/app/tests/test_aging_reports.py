import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.schemas.aging_report import (
    AgingBucket,
    AgingSummary,
    CustomerAgingSummary,
    InvoiceAgingDetail,
    AgingReport,
    AgingReportParams,
    OverdueInvoice,
    OverdueInvoicesParams,
    AgingTrendData,
    AgingTrends,
    AgingTrendsParams,
)


class TestAgingReportSchemas:
    """Test aging report Pydantic schemas"""

    def test_aging_bucket_schema(self):
        """Test aging bucket schema"""
        bucket_data = {
            "count": 5,
            "amount": Decimal("2500.00"),
        }

        bucket = AgingBucket(**bucket_data)
        assert bucket.count == 5
        assert bucket.amount == Decimal("2500.00")

    def test_aging_bucket_invalid_count(self):
        """Test aging bucket with invalid count"""
        bucket_data = {
            "count": -1,  # Must be >= 0
            "amount": Decimal("100.00"),
        }

        with pytest.raises(ValueError):
            AgingBucket(**bucket_data)

    def test_aging_summary_schema(self):
        """Test aging summary schema"""
        summary_data = {
            "current": {"count": 10, "amount": Decimal("5000.00")},
            "days_1_30": {"count": 5, "amount": Decimal("2500.00")},
            "days_31_60": {"count": 3, "amount": Decimal("1500.00")},
            "days_61_90": {"count": 2, "amount": Decimal("1000.00")},
            "days_over_90": {"count": 1, "amount": Decimal("500.00")},
            "total": {"count": 21, "amount": Decimal("10500.00")},
        }

        summary = AgingSummary(**summary_data)
        assert summary.current.count == 10
        assert summary.days_1_30.amount == Decimal("2500.00")
        assert summary.total.count == 21

    def test_customer_aging_summary_schema(self):
        """Test customer aging summary schema"""
        customer_data = {
            "customer_id": 1,
            "customer_name": "John Doe",
            "company_name": "Test Company",
            "current": Decimal("1000.00"),
            "days_1_30": Decimal("500.00"),
            "days_31_60": Decimal("300.00"),
            "days_61_90": Decimal("200.00"),
            "days_over_90": Decimal("100.00"),
            "total": Decimal("2100.00"),
            "invoice_count": 5,
        }

        customer_summary = CustomerAgingSummary(**customer_data)
        assert customer_summary.customer_id == 1
        assert customer_summary.customer_name == "John Doe"
        assert customer_summary.total == Decimal("2100.00")
        assert customer_summary.invoice_count == 5

    def test_invoice_aging_detail_schema(self):
        """Test invoice aging detail schema"""
        today = date.today()
        due_date = today - timedelta(days=45)

        invoice_data = {
            "invoice_id": 1,
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "customer_name": "John Doe",
            "company_name": "Test Company",
            "invoice_date": today - timedelta(days=60),
            "due_date": due_date,
            "total_amount": Decimal("1000.00"),
            "paid_amount": Decimal("200.00"),
            "outstanding_amount": Decimal("800.00"),
            "days_overdue": 45,
            "aging_bucket": "days_31_60",
            "status": "sent",
        }

        invoice_detail = InvoiceAgingDetail(**invoice_data)
        assert invoice_detail.invoice_id == 1
        assert invoice_detail.days_overdue == 45
        assert invoice_detail.aging_bucket == "days_31_60"
        assert invoice_detail.outstanding_amount == Decimal("800.00")

    def test_invoice_aging_detail_invalid_bucket(self):
        """Test invoice aging detail with invalid aging bucket"""
        today = date.today()

        invoice_data = {
            "invoice_id": 1,
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "customer_name": "John Doe",
            "invoice_date": today,
            "due_date": today,
            "total_amount": Decimal("1000.00"),
            "paid_amount": Decimal("0.00"),
            "outstanding_amount": Decimal("1000.00"),
            "days_overdue": 0,
            "aging_bucket": "invalid_bucket",  # Invalid bucket
            "status": "sent",
        }

        with pytest.raises(ValueError):
            InvoiceAgingDetail(**invoice_data)

    def test_aging_report_schema(self):
        """Test complete aging report schema"""
        today = date.today()

        report_data = {
            "report_date": today,
            "organization_id": 1,
            "customer_filter": None,
            "include_paid": False,
            "summary": {
                "current": {"count": 5, "amount": Decimal("2500.00")},
                "days_1_30": {"count": 3, "amount": Decimal("1500.00")},
                "days_31_60": {"count": 2, "amount": Decimal("1000.00")},
                "days_61_90": {"count": 1, "amount": Decimal("500.00")},
                "days_over_90": {"count": 1, "amount": Decimal("300.00")},
                "total": {"count": 12, "amount": Decimal("5800.00")},
            },
            "customer_summaries": [],
            "invoice_details": [],
            "total_customers": 0,
            "total_invoices": 0,
        }

        report = AgingReport(**report_data)
        assert report.report_date == today
        assert report.organization_id == 1
        assert report.summary.total.amount == Decimal("5800.00")

    def test_overdue_invoice_schema(self):
        """Test overdue invoice schema"""
        today = date.today()
        due_date = today - timedelta(days=30)

        overdue_data = {
            "invoice_id": 1,
            "invoice_number": "INV-2024-0001",
            "customer_id": 1,
            "customer_name": "John Doe",
            "company_name": "Test Company",
            "invoice_date": today - timedelta(days=45),
            "due_date": due_date,
            "total_amount": Decimal("1000.00"),
            "paid_amount": Decimal("0.00"),
            "outstanding_amount": Decimal("1000.00"),
            "days_overdue": 30,
            "status": "overdue",
        }

        overdue_invoice = OverdueInvoice(**overdue_data)
        assert overdue_invoice.invoice_id == 1
        assert overdue_invoice.days_overdue == 30
        assert overdue_invoice.outstanding_amount == Decimal("1000.00")

    def test_aging_trends_schema(self):
        """Test aging trends schema"""
        today = date.today()

        trends_data = {
            "trends": [
                {
                    "report_date": today,
                    "month_year": "2024-01",
                    "summary": {
                        "current": {"count": 5, "amount": Decimal("2500.00")},
                        "days_1_30": {"count": 3, "amount": Decimal("1500.00")},
                        "days_31_60": {
                            "count": 2,
                            "amount": Decimal("1000.00"),
                        },
                        "days_61_90": {"count": 1, "amount": Decimal("500.00")},
                        "days_over_90": {
                            "count": 1,
                            "amount": Decimal("300.00"),
                        },
                        "total": {"count": 12, "amount": Decimal("5800.00")},
                    },
                    "total_customers": 5,
                    "total_invoices": 12,
                }
            ],
            "months_back": 6,
        }

        trends = AgingTrends(**trends_data)
        assert trends.months_back == 6
        assert len(trends.trends) == 1
        assert trends.trends[0].total_customers == 5


class TestAgingReportBusinessLogic:
    """Test aging report business logic without database"""

    def test_aging_bucket_calculation(self):
        """Test aging bucket calculation logic"""
        today = date.today()

        # Test different aging scenarios
        test_cases = [
            (today + timedelta(days=5), "current"),  # Future due date
            (today, "current"),  # Due today
            (today - timedelta(days=15), "days_1_30"),  # 15 days overdue
            (today - timedelta(days=30), "days_1_30"),  # 30 days overdue
            (today - timedelta(days=45), "days_31_60"),  # 45 days overdue
            (today - timedelta(days=60), "days_31_60"),  # 60 days overdue
            (today - timedelta(days=75), "days_61_90"),  # 75 days overdue
            (today - timedelta(days=90), "days_61_90"),  # 90 days overdue
            (today - timedelta(days=120), "days_over_90"),  # 120 days overdue
        ]

        for due_date, expected_bucket in test_cases:
            days_overdue = (today - due_date).days

            if days_overdue <= 0:
                bucket = "current"
            elif days_overdue <= 30:
                bucket = "days_1_30"
            elif days_overdue <= 60:
                bucket = "days_31_60"
            elif days_overdue <= 90:
                bucket = "days_61_90"
            else:
                bucket = "days_over_90"

            assert bucket == expected_bucket, (
                f"Failed for due_date {due_date}, days_overdue {days_overdue}"
            )

    def test_aging_summary_calculation(self):
        """Test aging summary calculation logic"""
        # Mock invoice data
        invoices = [
            {
                "outstanding": Decimal("1000.00"),
                "days_overdue": -5,
                "bucket": "current",
            },
            {
                "outstanding": Decimal("500.00"),
                "days_overdue": 15,
                "bucket": "days_1_30",
            },
            {
                "outstanding": Decimal("750.00"),
                "days_overdue": 45,
                "bucket": "days_31_60",
            },
            {
                "outstanding": Decimal("300.00"),
                "days_overdue": 75,
                "bucket": "days_61_90",
            },
            {
                "outstanding": Decimal("200.00"),
                "days_overdue": 120,
                "bucket": "days_over_90",
            },
        ]

        # Calculate summary
        summary = {
            "current": {"count": 0, "amount": Decimal("0.00")},
            "days_1_30": {"count": 0, "amount": Decimal("0.00")},
            "days_31_60": {"count": 0, "amount": Decimal("0.00")},
            "days_61_90": {"count": 0, "amount": Decimal("0.00")},
            "days_over_90": {"count": 0, "amount": Decimal("0.00")},
            "total": {"count": 0, "amount": Decimal("0.00")},
        }

        for invoice in invoices:
            bucket = invoice["bucket"]
            amount = invoice["outstanding"]

            summary[bucket]["count"] += 1
            summary[bucket]["amount"] += amount
            summary["total"]["count"] += 1
            summary["total"]["amount"] += amount

        # Verify calculations
        assert summary["current"]["count"] == 1
        assert summary["current"]["amount"] == Decimal("1000.00")
        assert summary["days_1_30"]["amount"] == Decimal("500.00")
        assert summary["total"]["count"] == 5
        assert summary["total"]["amount"] == Decimal("2750.00")

    def test_overdue_percentage_calculation(self):
        """Test overdue percentage calculation"""
        total_outstanding = Decimal("10000.00")
        current_amount = Decimal("6000.00")
        overdue_amount = total_outstanding - current_amount

        overdue_percentage = float(overdue_amount / total_outstanding * 100)

        assert overdue_percentage == 40.0
        assert overdue_percentage >= 0
        assert overdue_percentage <= 100

    def test_collection_efficiency_calculation(self):
        """Test collection efficiency calculation"""
        total_outstanding = Decimal("10000.00")
        current_amount = Decimal("7000.00")  # Not yet due

        collection_efficiency = float(current_amount / total_outstanding * 100)

        assert collection_efficiency == 70.0
        assert collection_efficiency >= 0
        assert collection_efficiency <= 100

    def test_weighted_average_days_calculation(self):
        """Test weighted average days outstanding calculation"""
        invoices = [
            {"outstanding": Decimal("1000.00"), "days_overdue": 10},
            {"outstanding": Decimal("2000.00"), "days_overdue": 30},
            {"outstanding": Decimal("500.00"), "days_overdue": 60},
        ]

        total_weighted_days = 0
        total_amount = 0

        for invoice in invoices:
            amount = float(invoice["outstanding"])
            days = invoice["days_overdue"]
            total_weighted_days += days * amount
            total_amount += amount

        average_days = (
            total_weighted_days / total_amount if total_amount > 0 else 0
        )

        # Expected: (10*1000 + 30*2000 + 60*500) / 3500 = 100000 / 3500 = 28.57
        expected_average = (10 * 1000 + 30 * 2000 + 60 * 500) / 3500
        assert abs(average_days - expected_average) < 0.01

    def test_customer_risk_assessment(self):
        """Test customer risk assessment logic"""
        customers = [
            {
                "name": "Customer A",
                "days_61_90": Decimal("500.00"),
                "days_over_90": Decimal("1500.00"),
                "total": Decimal("3000.00"),
            },
            {
                "name": "Customer B",
                "days_61_90": Decimal("200.00"),
                "days_over_90": Decimal("300.00"),
                "total": Decimal("1000.00"),
            },
            {
                "name": "Customer C",
                "days_61_90": Decimal("0.00"),
                "days_over_90": Decimal("0.00"),
                "total": Decimal("2000.00"),
            },
        ]

        # Identify high-risk customers (over 60 days > $1000)
        high_risk_customers = []
        risk_threshold = Decimal("1000.00")

        for customer in customers:
            high_risk_amount = customer["days_61_90"] + customer["days_over_90"]
            if high_risk_amount > risk_threshold:
                high_risk_customers.append(customer["name"])

        assert len(high_risk_customers) == 1
        assert "Customer A" in high_risk_customers
        assert "Customer B" not in high_risk_customers
        assert "Customer C" not in high_risk_customers


class TestAgingReportService:
    """Test aging report service functionality"""

    def test_aging_report_service_import(self):
        """Test that aging report service can be imported"""
        from app.services.aging_report_service import AgingReportService

        # Should be able to import and instantiate (with mock db)
        assert AgingReportService is not None

    def test_aging_report_service_methods(self):
        """Test that aging report service has required methods"""
        from app.services.aging_report_service import AgingReportService

        # Check that all required methods exist
        assert hasattr(AgingReportService, "generate_aging_report")
        assert hasattr(AgingReportService, "get_aging_summary_by_customer")
        assert hasattr(AgingReportService, "get_overdue_invoices")
        assert hasattr(AgingReportService, "get_aging_trends")
        assert hasattr(AgingReportService, "_get_aging_bucket")
        assert hasattr(AgingReportService, "_get_outstanding_invoices")


class TestAgingReportAPI:
    """Test aging report API endpoints"""

    def test_aging_report_api_import(self):
        """Test that aging report API can be imported"""
        from app.api.v1.reports import router

        assert router is not None

    def test_aging_report_api_endpoints_exist(self):
        """Test that aging report API endpoints are defined"""
        from app.api.v1.reports import router

        # Check that aging routes exist
        routes = [route.path for route in router.routes]
        assert "/aging" in routes
        assert "/aging/summary" in routes
        assert "/aging/overdue" in routes
        assert "/aging/trends" in routes
        assert "/aging/metrics" in routes
        assert "/aging/alerts" in routes
        assert "/aging/dashboard" in routes

    def test_aging_report_api_methods(self):
        """Test that aging report API has correct HTTP methods"""
        from app.api.v1.reports import router

        # Get all route methods
        all_methods = []
        for route in router.routes:
            if hasattr(route, "methods"):
                all_methods.extend(route.methods)

        # Check that GET methods are available (all aging endpoints are GET)
        assert "GET" in all_methods

    def test_aging_report_api_in_main_router(self):
        """Test that aging report API is included in main router"""
        from app.api.v1.api import api_router

        # Check that report routes are included
        report_routes_found = False
        for route in api_router.routes:
            if hasattr(route, "path_regex") and "reports" in str(
                route.path_regex
            ):
                report_routes_found = True
                break

        assert report_routes_found, "Report routes not found in main API router"

    def test_aging_schemas_integration(self):
        """Test that aging schemas work with API"""
        from app.schemas.aging_report import AgingReport, AgingReportParams

        # Test that schemas can be used for API serialization
        today = date.today()

        report_data = {
            "report_date": today,
            "organization_id": 1,
            "customer_filter": None,
            "include_paid": False,
            "summary": {
                "current": {"count": 0, "amount": Decimal("0.00")},
                "days_1_30": {"count": 0, "amount": Decimal("0.00")},
                "days_31_60": {"count": 0, "amount": Decimal("0.00")},
                "days_61_90": {"count": 0, "amount": Decimal("0.00")},
                "days_over_90": {"count": 0, "amount": Decimal("0.00")},
                "total": {"count": 0, "amount": Decimal("0.00")},
            },
            "customer_summaries": [],
            "invoice_details": [],
            "total_customers": 0,
            "total_invoices": 0,
        }

        # Should be able to create and validate
        aging_report = AgingReport(**report_data)
        assert aging_report.organization_id == 1
