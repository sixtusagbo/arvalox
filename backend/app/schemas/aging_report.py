from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AgingBucket(BaseModel):
    """Schema for aging bucket data"""

    count: int = Field(
        ..., ge=0, description="Number of invoices in this bucket"
    )
    amount: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Total amount in this bucket"
    )


class AgingSummary(BaseModel):
    """Schema for aging summary data"""

    current: AgingBucket = Field(..., description="Current (not yet due)")
    days_1_30: AgingBucket = Field(..., description="1-30 days overdue")
    days_31_60: AgingBucket = Field(..., description="31-60 days overdue")
    days_61_90: AgingBucket = Field(..., description="61-90 days overdue")
    days_over_90: AgingBucket = Field(..., description="Over 90 days overdue")
    total: AgingBucket = Field(..., description="Total outstanding")


class CustomerAgingSummary(BaseModel):
    """Schema for customer aging summary"""

    customer_id: int
    customer_name: str
    company_name: Optional[str] = None
    current: Decimal = Field(..., decimal_places=2)
    days_1_30: Decimal = Field(..., decimal_places=2)
    days_31_60: Decimal = Field(..., decimal_places=2)
    days_61_90: Decimal = Field(..., decimal_places=2)
    days_over_90: Decimal = Field(..., decimal_places=2)
    total: Decimal = Field(..., decimal_places=2)
    invoice_count: int = Field(..., ge=0)


class InvoiceAgingDetail(BaseModel):
    """Schema for individual invoice aging detail"""

    invoice_id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    company_name: Optional[str] = None
    invoice_date: date
    due_date: date
    total_amount: Decimal = Field(..., decimal_places=2)
    paid_amount: Decimal = Field(..., decimal_places=2)
    outstanding_amount: Decimal = Field(..., decimal_places=2)
    days_overdue: int
    aging_bucket: str = Field(
        ..., pattern="^(current|days_1_30|days_31_60|days_61_90|days_over_90)$"
    )
    status: str


class AgingReport(BaseModel):
    """Schema for complete aging report"""

    report_date: date
    organization_id: int
    customer_filter: Optional[int] = None
    include_paid: bool = False
    summary: AgingSummary
    customer_summaries: List[CustomerAgingSummary]
    invoice_details: List[InvoiceAgingDetail]
    total_customers: int = Field(..., ge=0)
    total_invoices: int = Field(..., ge=0)


class AgingReportParams(BaseModel):
    """Schema for aging report parameters"""

    as_of_date: Optional[date] = Field(
        None, description="Date to calculate aging as of (defaults to today)"
    )
    customer_id: Optional[int] = Field(
        None, gt=0, description="Filter by specific customer"
    )
    include_paid: bool = Field(False, description="Include fully paid invoices")


class OverdueInvoice(BaseModel):
    """Schema for overdue invoice data"""

    invoice_id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    company_name: Optional[str] = None
    invoice_date: date
    due_date: date
    total_amount: Decimal = Field(..., decimal_places=2)
    paid_amount: Decimal = Field(..., decimal_places=2)
    outstanding_amount: Decimal = Field(..., decimal_places=2)
    days_overdue: int = Field(..., ge=0)
    status: str


class OverdueInvoicesParams(BaseModel):
    """Schema for overdue invoices parameters"""

    days_overdue: int = Field(1, ge=1, description="Minimum days overdue")
    customer_id: Optional[int] = Field(
        None, gt=0, description="Filter by specific customer"
    )


class AgingTrendData(BaseModel):
    """Schema for aging trend data point"""

    report_date: date
    month_year: str
    summary: AgingSummary
    total_customers: int = Field(..., ge=0)
    total_invoices: int = Field(..., ge=0)


class AgingTrends(BaseModel):
    """Schema for aging trends response"""

    trends: List[AgingTrendData]
    months_back: int = Field(..., ge=1)


class AgingTrendsParams(BaseModel):
    """Schema for aging trends parameters"""

    months_back: int = Field(
        6, ge=1, le=24, description="Number of months to look back"
    )


class AgingMetrics(BaseModel):
    """Schema for aging metrics and KPIs"""

    total_outstanding: Decimal = Field(..., decimal_places=2)
    total_overdue: Decimal = Field(..., decimal_places=2)
    overdue_percentage: float = Field(..., ge=0, le=100)
    average_days_outstanding: float = Field(..., ge=0)
    worst_aging_customer: Optional[str] = None
    worst_aging_amount: Optional[Decimal] = None
    collection_efficiency: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of receivables collected on time",
    )


class AgingAnalytics(BaseModel):
    """Schema for comprehensive aging analytics"""

    report_date: date
    organization_id: int
    metrics: AgingMetrics
    aging_distribution: AgingSummary
    top_overdue_customers: List[CustomerAgingSummary]
    critical_invoices: List[InvoiceAgingDetail]  # Over 90 days


class AgingExportParams(BaseModel):
    """Schema for aging report export parameters"""

    format: str = Field(
        "csv", pattern="^(csv|pdf|excel)$", description="Export format"
    )
    as_of_date: Optional[date] = Field(
        None, description="Date to calculate aging as of"
    )
    customer_id: Optional[int] = Field(
        None, gt=0, description="Filter by specific customer"
    )
    include_paid: bool = Field(False, description="Include fully paid invoices")
    include_details: bool = Field(True, description="Include invoice details")
    include_summary: bool = Field(True, description="Include aging summary")


class AgingAlerts(BaseModel):
    """Schema for aging-based alerts"""

    critical_overdue_count: int = Field(
        ..., ge=0, description="Invoices over 90 days"
    )
    critical_overdue_amount: Decimal = Field(..., decimal_places=2)
    new_overdue_count: int = Field(
        ..., ge=0, description="Newly overdue invoices"
    )
    new_overdue_amount: Decimal = Field(..., decimal_places=2)
    collection_risk_customers: List[str] = Field(
        ..., description="Customers with high collection risk"
    )
    total_at_risk_amount: Decimal = Field(..., decimal_places=2)


class AgingDashboard(BaseModel):
    """Schema for aging dashboard data"""

    report_date: date
    organization_id: int
    metrics: AgingMetrics
    alerts: AgingAlerts
    aging_summary: AgingSummary
    recent_trends: List[AgingTrendData]
    top_customers_by_outstanding: List[CustomerAgingSummary]


class AgingComparisonPeriod(BaseModel):
    """Schema for aging comparison between periods"""

    period_label: str
    report_date: date
    summary: AgingSummary
    metrics: AgingMetrics


class AgingComparison(BaseModel):
    """Schema for aging comparison report"""

    current_period: AgingComparisonPeriod
    previous_period: AgingComparisonPeriod
    changes: Dict[str, Decimal] = Field(
        ..., description="Changes between periods"
    )
    improvement_areas: List[str] = Field(
        ..., description="Areas showing improvement"
    )
    concern_areas: List[str] = Field(..., description="Areas of concern")


class AgingForecast(BaseModel):
    """Schema for aging forecast data"""

    forecast_date: date
    predicted_overdue_amount: Decimal = Field(..., decimal_places=2)
    predicted_collection_rate: float = Field(..., ge=0, le=100)
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    recommended_actions: List[str] = Field(
        ..., description="Recommended collection actions"
    )
