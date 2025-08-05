from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ExportParams(BaseModel):
    """Base schema for export parameters"""
    format: str = Field("csv", pattern="^(csv|pdf|excel)$", description="Export format")
    date_from: Optional[date] = Field(None, description="Start date for export data")
    date_to: Optional[date] = Field(None, description="End date for export data")


class AgingReportExportParams(ExportParams):
    """Schema for aging report export parameters"""
    customer_id: Optional[int] = Field(None, gt=0, description="Filter by specific customer")
    include_paid: bool = Field(False, description="Include fully paid invoices")
    as_of_date: Optional[date] = Field(None, description="Date to calculate aging as of")


class PaymentHistoryExportParams(ExportParams):
    """Schema for payment history export parameters"""
    customer_id: Optional[int] = Field(None, gt=0, description="Filter by specific customer")
    payment_method: Optional[str] = Field(None, description="Filter by payment method")
    status: Optional[str] = Field(None, description="Filter by payment status")
    limit: int = Field(1000, ge=1, le=10000, description="Maximum number of records to export")


class DashboardExportParams(ExportParams):
    """Schema for dashboard export parameters"""
    include_charts: bool = Field(True, description="Include charts in PDF export")
    include_summary: bool = Field(True, description="Include summary metrics")
    include_top_customers: bool = Field(True, description="Include top customers data")
    include_recent_activity: bool = Field(True, description="Include recent activity")


class InvoiceExportParams(ExportParams):
    """Schema for invoice export parameters"""
    customer_id: Optional[int] = Field(None, gt=0, description="Filter by specific customer")
    status: Optional[str] = Field(None, description="Filter by invoice status")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum invoice amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum invoice amount")
    overdue_only: bool = Field(False, description="Export only overdue invoices")
    limit: int = Field(1000, ge=1, le=10000, description="Maximum number of records to export")


class CustomerExportParams(ExportParams):
    """Schema for customer export parameters"""
    status: Optional[str] = Field(None, description="Filter by customer status")
    has_outstanding: Optional[bool] = Field(None, description="Filter customers with outstanding balances")
    include_contact_info: bool = Field(True, description="Include contact information")
    include_financial_summary: bool = Field(True, description="Include financial summary")


class ExportResponse(BaseModel):
    """Schema for export response"""
    filename: str = Field(..., description="Generated filename for the export")
    content_type: str = Field(..., description="MIME type of the exported file")
    size_bytes: int = Field(..., ge=0, description="Size of the exported file in bytes")
    export_date: date = Field(..., description="Date when export was generated")
    record_count: Optional[int] = Field(None, ge=0, description="Number of records exported")


class ExportJob(BaseModel):
    """Schema for export job tracking"""
    job_id: str = Field(..., description="Unique identifier for the export job")
    export_type: str = Field(..., description="Type of export (aging_report, payment_history, etc.)")
    format: str = Field(..., pattern="^(csv|pdf|excel)$", description="Export format")
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$", description="Job status")
    organization_id: int = Field(..., gt=0, description="Organization ID")
    created_at: date = Field(..., description="When the job was created")
    completed_at: Optional[date] = Field(None, description="When the job was completed")
    file_url: Optional[str] = Field(None, description="URL to download the exported file")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    parameters: dict = Field(..., description="Export parameters used for the job")


class BulkExportParams(BaseModel):
    """Schema for bulk export parameters"""
    export_types: list[str] = Field(..., min_items=1, description="List of export types to include")
    format: str = Field("csv", pattern="^(csv|pdf|excel)$", description="Export format")
    date_from: Optional[date] = Field(None, description="Start date for all exports")
    date_to: Optional[date] = Field(None, description="End date for all exports")
    compress: bool = Field(True, description="Compress multiple files into a ZIP archive")


class ExportStatistics(BaseModel):
    """Schema for export statistics"""
    total_exports: int = Field(..., ge=0, description="Total number of exports")
    exports_by_type: dict[str, int] = Field(..., description="Export count by type")
    exports_by_format: dict[str, int] = Field(..., description="Export count by format")
    total_size_bytes: int = Field(..., ge=0, description="Total size of all exports")
    most_popular_export: Optional[str] = Field(None, description="Most frequently exported type")
    average_export_size: float = Field(..., ge=0, description="Average export size in bytes")


class ExportTemplate(BaseModel):
    """Schema for export template configuration"""
    template_id: str = Field(..., description="Unique identifier for the template")
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    export_type: str = Field(..., description="Type of export this template is for")
    format: str = Field(..., pattern="^(csv|pdf|excel)$", description="Export format")
    parameters: dict = Field(..., description="Default parameters for this template")
    columns: Optional[list[str]] = Field(None, description="Specific columns to include (for CSV/Excel)")
    is_default: bool = Field(False, description="Whether this is the default template")
    created_by: int = Field(..., gt=0, description="User ID who created the template")
    organization_id: int = Field(..., gt=0, description="Organization ID")


class ExportSchedule(BaseModel):
    """Schema for scheduled exports"""
    schedule_id: str = Field(..., description="Unique identifier for the schedule")
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    export_type: str = Field(..., description="Type of export to schedule")
    format: str = Field(..., pattern="^(csv|pdf|excel)$", description="Export format")
    frequency: str = Field(..., pattern="^(daily|weekly|monthly|quarterly)$", description="Export frequency")
    parameters: dict = Field(..., description="Export parameters")
    email_recipients: list[str] = Field(..., min_items=1, description="Email addresses to send exports to")
    is_active: bool = Field(True, description="Whether the schedule is active")
    next_run_date: date = Field(..., description="Next scheduled run date")
    last_run_date: Optional[date] = Field(None, description="Last run date")
    organization_id: int = Field(..., gt=0, description="Organization ID")


class ExportAuditLog(BaseModel):
    """Schema for export audit logging"""
    log_id: str = Field(..., description="Unique identifier for the log entry")
    export_type: str = Field(..., description="Type of export")
    format: str = Field(..., description="Export format")
    user_id: int = Field(..., gt=0, description="User who performed the export")
    organization_id: int = Field(..., gt=0, description="Organization ID")
    parameters: dict = Field(..., description="Export parameters used")
    record_count: int = Field(..., ge=0, description="Number of records exported")
    file_size_bytes: int = Field(..., ge=0, description="Size of exported file")
    export_date: date = Field(..., description="Date of export")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")


class ExportPermissions(BaseModel):
    """Schema for export permissions"""
    can_export_aging_reports: bool = Field(True, description="Permission to export aging reports")
    can_export_payment_history: bool = Field(True, description="Permission to export payment history")
    can_export_dashboard_data: bool = Field(True, description="Permission to export dashboard data")
    can_export_invoices: bool = Field(True, description="Permission to export invoices")
    can_export_customers: bool = Field(True, description="Permission to export customers")
    can_schedule_exports: bool = Field(False, description="Permission to schedule automated exports")
    can_create_templates: bool = Field(False, description="Permission to create export templates")
    max_records_per_export: int = Field(10000, ge=1, description="Maximum records allowed per export")
    max_exports_per_day: int = Field(50, ge=1, description="Maximum exports allowed per day")


class ExportQuota(BaseModel):
    """Schema for export quota tracking"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    user_id: int = Field(..., gt=0, description="User ID")
    exports_today: int = Field(..., ge=0, description="Number of exports performed today")
    exports_this_month: int = Field(..., ge=0, description="Number of exports performed this month")
    total_size_today_bytes: int = Field(..., ge=0, description="Total size of exports today")
    total_size_this_month_bytes: int = Field(..., ge=0, description="Total size of exports this month")
    last_export_date: Optional[date] = Field(None, description="Date of last export")
    quota_exceeded: bool = Field(False, description="Whether quota has been exceeded")


class ExportConfiguration(BaseModel):
    """Schema for export system configuration"""
    max_file_size_mb: int = Field(100, ge=1, le=1000, description="Maximum file size in MB")
    max_records_per_export: int = Field(10000, ge=1, description="Maximum records per export")
    supported_formats: list[str] = Field(["csv", "pdf", "excel"], description="Supported export formats")
    default_format: str = Field("csv", description="Default export format")
    enable_compression: bool = Field(True, description="Enable file compression")
    retention_days: int = Field(30, ge=1, le=365, description="Days to retain exported files")
    enable_email_delivery: bool = Field(True, description="Enable email delivery of exports")
    enable_scheduled_exports: bool = Field(True, description="Enable scheduled exports")
    max_concurrent_exports: int = Field(5, ge=1, le=20, description="Maximum concurrent export jobs")
