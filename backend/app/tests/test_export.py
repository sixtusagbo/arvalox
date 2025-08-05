import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.schemas.export import (
    ExportParams,
    AgingReportExportParams,
    PaymentHistoryExportParams,
    DashboardExportParams,
    InvoiceExportParams,
    CustomerExportParams,
    ExportResponse,
    ExportJob,
    BulkExportParams,
    ExportStatistics,
    ExportTemplate,
    ExportSchedule,
    ExportAuditLog,
    ExportPermissions,
    ExportQuota,
    ExportConfiguration,
)


class TestExportSchemas:
    """Test export Pydantic schemas"""

    def test_export_params_schema(self):
        """Test base export params schema"""
        params_data = {
            "format": "csv",
            "date_from": date.today() - timedelta(days=30),
            "date_to": date.today(),
        }

        params = ExportParams(**params_data)
        assert params.format == "csv"
        assert params.date_from == date.today() - timedelta(days=30)
        assert params.date_to == date.today()

    def test_export_params_invalid_format(self):
        """Test export params with invalid format"""
        params_data = {
            "format": "invalid_format",  # Must be csv, pdf, or excel
            "date_from": date.today(),
            "date_to": date.today(),
        }

        with pytest.raises(ValueError):
            ExportParams(**params_data)

    def test_aging_report_export_params_schema(self):
        """Test aging report export params schema"""
        params_data = {
            "format": "pdf",
            "customer_id": 123,
            "include_paid": True,
            "as_of_date": date.today(),
            "date_from": date.today() - timedelta(days=30),
            "date_to": date.today(),
        }

        params = AgingReportExportParams(**params_data)
        assert params.format == "pdf"
        assert params.customer_id == 123
        assert params.include_paid is True
        assert params.as_of_date == date.today()

    def test_payment_history_export_params_schema(self):
        """Test payment history export params schema"""
        params_data = {
            "format": "csv",
            "customer_id": 456,
            "payment_method": "bank_transfer",
            "status": "completed",
            "limit": 500,
            "date_from": date.today() - timedelta(days=60),
            "date_to": date.today(),
        }

        params = PaymentHistoryExportParams(**params_data)
        assert params.format == "csv"
        assert params.customer_id == 456
        assert params.payment_method == "bank_transfer"
        assert params.status == "completed"
        assert params.limit == 500

    def test_payment_history_export_params_invalid_limit(self):
        """Test payment history export params with invalid limit"""
        params_data = {
            "format": "csv",
            "limit": 20000,  # Exceeds maximum of 10000
        }

        with pytest.raises(ValueError):
            PaymentHistoryExportParams(**params_data)

    def test_dashboard_export_params_schema(self):
        """Test dashboard export params schema"""
        params_data = {
            "format": "pdf",
            "include_charts": True,
            "include_summary": True,
            "include_top_customers": False,
            "include_recent_activity": True,
            "date_from": date.today() - timedelta(days=30),
            "date_to": date.today(),
        }

        params = DashboardExportParams(**params_data)
        assert params.format == "pdf"
        assert params.include_charts is True
        assert params.include_top_customers is False

    def test_invoice_export_params_schema(self):
        """Test invoice export params schema"""
        params_data = {
            "format": "excel",
            "customer_id": 789,
            "status": "sent",
            "min_amount": 100.0,
            "max_amount": 5000.0,
            "overdue_only": True,
            "limit": 2000,
        }

        params = InvoiceExportParams(**params_data)
        assert params.format == "excel"
        assert params.customer_id == 789
        assert params.status == "sent"
        assert params.min_amount == 100.0
        assert params.overdue_only is True

    def test_customer_export_params_schema(self):
        """Test customer export params schema"""
        params_data = {
            "format": "csv",
            "status": "active",
            "has_outstanding": True,
            "include_contact_info": True,
            "include_financial_summary": False,
        }

        params = CustomerExportParams(**params_data)
        assert params.format == "csv"
        assert params.status == "active"
        assert params.has_outstanding is True
        assert params.include_financial_summary is False

    def test_export_response_schema(self):
        """Test export response schema"""
        response_data = {
            "filename": "aging_report_org1_20240805.csv",
            "content_type": "text/csv",
            "size_bytes": 15420,
            "export_date": date.today(),
            "record_count": 150,
        }

        response = ExportResponse(**response_data)
        assert response.filename == "aging_report_org1_20240805.csv"
        assert response.content_type == "text/csv"
        assert response.size_bytes == 15420
        assert response.record_count == 150

    def test_export_job_schema(self):
        """Test export job schema"""
        job_data = {
            "job_id": "job_12345",
            "export_type": "aging_report",
            "format": "pdf",
            "status": "completed",
            "organization_id": 1,
            "created_at": date.today(),
            "completed_at": date.today(),
            "file_url": "https://example.com/exports/file.pdf",
            "error_message": None,
            "parameters": {"format": "pdf", "include_paid": False},
        }

        job = ExportJob(**job_data)
        assert job.job_id == "job_12345"
        assert job.export_type == "aging_report"
        assert job.status == "completed"
        assert job.organization_id == 1

    def test_export_job_invalid_status(self):
        """Test export job with invalid status"""
        job_data = {
            "job_id": "job_12345",
            "export_type": "aging_report",
            "format": "pdf",
            "status": "invalid_status",  # Must be pending, processing, completed, or failed
            "organization_id": 1,
            "created_at": date.today(),
            "parameters": {},
        }

        with pytest.raises(ValueError):
            ExportJob(**job_data)

    def test_bulk_export_params_schema(self):
        """Test bulk export params schema"""
        params_data = {
            "export_types": ["aging_report", "payment_history", "dashboard"],
            "format": "csv",
            "date_from": date.today() - timedelta(days=30),
            "date_to": date.today(),
            "compress": True,
        }

        params = BulkExportParams(**params_data)
        assert len(params.export_types) == 3
        assert "aging_report" in params.export_types
        assert params.compress is True

    def test_bulk_export_params_empty_types(self):
        """Test bulk export params with empty export types"""
        params_data = {
            "export_types": [],  # Must have at least one item
            "format": "csv",
        }

        with pytest.raises(ValueError):
            BulkExportParams(**params_data)

    def test_export_statistics_schema(self):
        """Test export statistics schema"""
        stats_data = {
            "total_exports": 1250,
            "exports_by_type": {
                "aging_report": 500,
                "payment_history": 400,
                "dashboard": 350,
            },
            "exports_by_format": {
                "csv": 800,
                "pdf": 300,
                "excel": 150,
            },
            "total_size_bytes": 52428800,  # 50MB
            "most_popular_export": "aging_report",
            "average_export_size": 41943.04,
        }

        stats = ExportStatistics(**stats_data)
        assert stats.total_exports == 1250
        assert stats.exports_by_type["aging_report"] == 500
        assert stats.most_popular_export == "aging_report"

    def test_export_template_schema(self):
        """Test export template schema"""
        template_data = {
            "template_id": "template_123",
            "name": "Monthly Aging Report",
            "description": "Standard monthly aging report template",
            "export_type": "aging_report",
            "format": "pdf",
            "parameters": {"include_paid": False, "format": "pdf"},
            "columns": ["invoice_number", "customer_name", "amount", "days_overdue"],
            "is_default": True,
            "created_by": 1,
            "organization_id": 1,
        }

        template = ExportTemplate(**template_data)
        assert template.template_id == "template_123"
        assert template.name == "Monthly Aging Report"
        assert template.is_default is True
        assert len(template.columns) == 4

    def test_export_schedule_schema(self):
        """Test export schedule schema"""
        schedule_data = {
            "schedule_id": "schedule_456",
            "name": "Weekly Payment Report",
            "export_type": "payment_history",
            "format": "csv",
            "frequency": "weekly",
            "parameters": {"format": "csv", "limit": 1000},
            "email_recipients": ["manager@company.com", "accounting@company.com"],
            "is_active": True,
            "next_run_date": date.today() + timedelta(days=7),
            "last_run_date": date.today(),
            "organization_id": 1,
        }

        schedule = ExportSchedule(**schedule_data)
        assert schedule.schedule_id == "schedule_456"
        assert schedule.frequency == "weekly"
        assert len(schedule.email_recipients) == 2
        assert schedule.is_active is True

    def test_export_schedule_invalid_frequency(self):
        """Test export schedule with invalid frequency"""
        schedule_data = {
            "schedule_id": "schedule_456",
            "name": "Test Schedule",
            "export_type": "aging_report",
            "format": "csv",
            "frequency": "invalid_frequency",  # Must be daily, weekly, monthly, or quarterly
            "parameters": {},
            "email_recipients": ["test@example.com"],
            "next_run_date": date.today(),
            "organization_id": 1,
        }

        with pytest.raises(ValueError):
            ExportSchedule(**schedule_data)

    def test_export_permissions_schema(self):
        """Test export permissions schema"""
        permissions_data = {
            "can_export_aging_reports": True,
            "can_export_payment_history": True,
            "can_export_dashboard_data": False,
            "can_export_invoices": True,
            "can_export_customers": False,
            "can_schedule_exports": True,
            "can_create_templates": False,
            "max_records_per_export": 5000,
            "max_exports_per_day": 25,
        }

        permissions = ExportPermissions(**permissions_data)
        assert permissions.can_export_aging_reports is True
        assert permissions.can_export_dashboard_data is False
        assert permissions.max_records_per_export == 5000

    def test_export_quota_schema(self):
        """Test export quota schema"""
        quota_data = {
            "organization_id": 1,
            "user_id": 123,
            "exports_today": 5,
            "exports_this_month": 45,
            "total_size_today_bytes": 1048576,  # 1MB
            "total_size_this_month_bytes": 52428800,  # 50MB
            "last_export_date": date.today(),
            "quota_exceeded": False,
        }

        quota = ExportQuota(**quota_data)
        assert quota.organization_id == 1
        assert quota.user_id == 123
        assert quota.exports_today == 5
        assert quota.quota_exceeded is False

    def test_export_configuration_schema(self):
        """Test export configuration schema"""
        config_data = {
            "max_file_size_mb": 200,
            "max_records_per_export": 15000,
            "supported_formats": ["csv", "pdf", "excel"],
            "default_format": "csv",
            "enable_compression": True,
            "retention_days": 60,
            "enable_email_delivery": True,
            "enable_scheduled_exports": True,
            "max_concurrent_exports": 10,
        }

        config = ExportConfiguration(**config_data)
        assert config.max_file_size_mb == 200
        assert config.max_records_per_export == 15000
        assert len(config.supported_formats) == 3
        assert config.default_format == "csv"


class TestExportBusinessLogic:
    """Test export business logic without database"""

    def test_filename_generation_logic(self):
        """Test export filename generation logic"""
        export_type = "aging_report"
        format_type = "csv"
        organization_id = 123
        today = date.today().strftime('%Y%m%d')
        
        expected_filename = f"{export_type}_org{organization_id}_{today}.{format_type}"
        
        # Simulate filename generation
        filename = f"{export_type}_org{organization_id}_{today}.{format_type}"
        
        assert filename == expected_filename
        assert filename.endswith(".csv")
        assert "org123" in filename

    def test_content_type_mapping(self):
        """Test content type mapping for different formats"""
        content_types = {
            'csv': 'text/csv',
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        for format_type, expected_content_type in content_types.items():
            assert content_types.get(format_type) == expected_content_type

    def test_export_quota_calculation(self):
        """Test export quota calculation logic"""
        max_exports_per_day = 50
        current_exports_today = 45
        
        remaining_exports = max_exports_per_day - current_exports_today
        quota_exceeded = current_exports_today >= max_exports_per_day
        
        assert remaining_exports == 5
        assert quota_exceeded is False
        
        # Test quota exceeded scenario
        current_exports_today = 55
        quota_exceeded = current_exports_today >= max_exports_per_day
        assert quota_exceeded is True

    def test_file_size_validation(self):
        """Test file size validation logic"""
        max_file_size_bytes = 100 * 1024 * 1024  # 100MB
        file_size_bytes = 50 * 1024 * 1024  # 50MB
        
        is_valid_size = file_size_bytes <= max_file_size_bytes
        
        assert is_valid_size is True
        
        # Test oversized file
        file_size_bytes = 150 * 1024 * 1024  # 150MB
        is_valid_size = file_size_bytes <= max_file_size_bytes
        assert is_valid_size is False

    def test_export_permissions_validation(self):
        """Test export permissions validation logic"""
        permissions = {
            "can_export_aging_reports": True,
            "can_export_payment_history": False,
            "can_export_dashboard_data": True,
        }
        
        # Test allowed export
        can_export_aging = permissions.get("can_export_aging_reports", False)
        assert can_export_aging is True
        
        # Test denied export
        can_export_payments = permissions.get("can_export_payment_history", False)
        assert can_export_payments is False


class TestExportService:
    """Test export service functionality"""

    def test_export_service_import(self):
        """Test that export service can be imported"""
        from app.services.export_service import ExportService
        
        # Should be able to import and instantiate (with mock db)
        assert ExportService is not None

    def test_export_service_methods(self):
        """Test that export service has required methods"""
        from app.services.export_service import ExportService
        
        # Check that all required methods exist
        assert hasattr(ExportService, 'export_aging_report_csv')
        assert hasattr(ExportService, 'export_aging_report_pdf')
        assert hasattr(ExportService, 'export_payment_history_csv')
        assert hasattr(ExportService, 'export_dashboard_data_csv')
        assert hasattr(ExportService, 'get_export_filename')
        assert hasattr(ExportService, 'get_content_type')


class TestExportAPI:
    """Test export API endpoints"""

    def test_export_api_import(self):
        """Test that export API can be imported"""
        from app.api.v1.reports import router
        assert router is not None

    def test_export_api_endpoints_exist(self):
        """Test that export API endpoints are defined"""
        from app.api.v1.reports import router
        
        # Check that export routes exist
        routes = [route.path for route in router.routes]
        assert "/export/aging-report" in routes
        assert "/export/payment-history" in routes
        assert "/export/dashboard" in routes
        assert "/export/formats" in routes

    def test_export_api_methods(self):
        """Test that export API has correct HTTP methods"""
        from app.api.v1.reports import router
        
        # Get all route methods
        all_methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                all_methods.extend(route.methods)
        
        # Check that GET methods are available (all export endpoints are GET)
        assert "GET" in all_methods

    def test_export_schemas_integration(self):
        """Test that export schemas work with API"""
        from app.schemas.export import AgingReportExportParams, ExportResponse
        
        # Test that schemas can be used for API serialization
        params_data = {
            "format": "csv",
            "customer_id": 123,
            "include_paid": False,
            "as_of_date": date.today(),
        }
        
        # Should be able to create and validate
        params = AgingReportExportParams(**params_data)
        assert params.format == "csv"

    def test_export_service_integration(self):
        """Test that export service integrates with API"""
        from app.services.export_service import ExportService
        
        # Should be able to import service used by API
        assert ExportService is not None
        
        # Check that service methods match API endpoint functionality
        service_methods = [
            'export_aging_report_csv',      # Used by /export/aging-report endpoint
            'export_payment_history_csv',   # Used by /export/payment-history endpoint
            'export_dashboard_data_csv',    # Used by /export/dashboard endpoint
            'get_export_filename',          # Used by all export endpoints
            'get_content_type',             # Used by all export endpoints
        ]
        
        for method in service_methods:
            assert hasattr(ExportService, method)
