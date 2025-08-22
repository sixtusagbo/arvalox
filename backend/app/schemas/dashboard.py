from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """Schema for date range"""
    from_date: date = Field(..., alias="from")
    to: date


class RevenueMetrics(BaseModel):
    """Schema for revenue metrics"""
    total_revenue: Decimal = Field(..., decimal_places=2)
    invoice_count: int = Field(..., ge=0)
    average_invoice_value: Decimal = Field(..., decimal_places=2)
    outstanding_amount: Decimal = Field(..., decimal_places=2)
    outstanding_count: int = Field(..., ge=0)
    revenue_growth_percentage: float
    previous_period_revenue: Decimal = Field(..., decimal_places=2)


class StatusBreakdown(BaseModel):
    """Schema for status breakdown"""
    count: int = Field(..., ge=0)
    amount: Decimal = Field(..., decimal_places=2)


class InvoiceMetrics(BaseModel):
    """Schema for invoice metrics"""
    status_breakdown: Dict[str, StatusBreakdown]
    overdue_count: int = Field(..., ge=0)
    overdue_amount: Decimal = Field(..., decimal_places=2)


class PaymentMethodBreakdown(BaseModel):
    """Schema for payment method breakdown"""
    count: int = Field(..., ge=0)
    amount: Decimal = Field(..., decimal_places=2)


class PaymentMetrics(BaseModel):
    """Schema for payment metrics"""
    payment_count: int = Field(..., ge=0)
    total_payments: Decimal = Field(..., decimal_places=2)
    average_payment: Decimal = Field(..., decimal_places=2)
    method_breakdown: Dict[str, PaymentMethodBreakdown]


class CustomerMetrics(BaseModel):
    """Schema for customer metrics"""
    total_customers: int = Field(..., ge=0)
    active_customers: int = Field(..., ge=0)
    inactive_customers: int = Field(..., ge=0)
    customers_with_outstanding: int = Field(..., ge=0)


class AgingBucketMetrics(BaseModel):
    """Schema for aging bucket metrics"""
    count: int = Field(..., ge=0)
    amount: Decimal = Field(..., decimal_places=2)


class AgingMetrics(BaseModel):
    """Schema for aging metrics"""
    total_outstanding: Decimal = Field(..., decimal_places=2)
    total_overdue: Decimal = Field(..., decimal_places=2)
    overdue_percentage: float = Field(..., ge=0, le=100)
    collection_efficiency: float = Field(..., ge=0, le=100)
    aging_breakdown: Dict[str, AgingBucketMetrics]


class RecentActivity(BaseModel):
    """Schema for recent activity item"""
    type: str = Field(..., pattern="^(invoice|payment)$")
    id: int
    description: str
    amount: Decimal = Field(..., decimal_places=2)
    date: datetime
    status: str


class TopCustomer(BaseModel):
    """Schema for top customer"""
    customer_id: int
    name: str
    company_name: Optional[str] = None
    total_revenue: Decimal = Field(..., decimal_places=2)
    invoice_count: int = Field(..., ge=0)
    outstanding_amount: Decimal = Field(..., decimal_places=2)


class DashboardOverview(BaseModel):
    """Schema for complete dashboard overview"""
    organization_id: int
    date_range: DateRange
    revenue_metrics: RevenueMetrics
    invoice_metrics: InvoiceMetrics
    payment_metrics: PaymentMetrics
    customer_metrics: CustomerMetrics
    aging_metrics: AgingMetrics
    recent_activity: List[RecentActivity]
    top_customers: List[TopCustomer]
    generated_at: datetime


class DashboardParams(BaseModel):
    """Schema for dashboard parameters"""
    date_from: Optional[date] = Field(None, description="Start date for metrics (defaults to 30 days ago)")
    date_to: Optional[date] = Field(None, description="End date for metrics (defaults to today)")


class KPISummary(BaseModel):
    """Schema for KPI summary"""
    total_revenue: Decimal = Field(..., decimal_places=2)
    outstanding_amount: Decimal = Field(..., decimal_places=2)
    overdue_amount: Decimal = Field(..., decimal_places=2)
    collection_efficiency: float = Field(..., ge=0, le=100)
    revenue_growth: float
    total_customers: int = Field(..., ge=0)
    active_invoices: int = Field(..., ge=0)
    overdue_invoices: int = Field(..., ge=0)


class QuickStats(BaseModel):
    """Schema for quick dashboard stats"""
    total_revenue_this_month: Decimal = Field(..., decimal_places=2)
    total_outstanding: Decimal = Field(..., decimal_places=2)
    overdue_amount: Decimal = Field(..., decimal_places=2)
    total_customers: int = Field(..., ge=0)
    invoices_this_month: int = Field(..., ge=0)
    payments_this_month: int = Field(..., ge=0)


class TrendData(BaseModel):
    """Schema for trend data point"""
    period: str
    revenue: Decimal = Field(..., decimal_places=2)
    payments: Decimal = Field(..., decimal_places=2)
    outstanding: Decimal = Field(..., decimal_places=2)


class DashboardTrends(BaseModel):
    """Schema for dashboard trends"""
    revenue_trend: List[TrendData]
    payment_trend: List[TrendData]
    outstanding_trend: List[TrendData]


class AlertItem(BaseModel):
    """Schema for dashboard alert"""
    type: str = Field(..., pattern="^(warning|error|info)$")
    title: str
    message: str
    count: Optional[int] = None
    amount: Optional[Decimal] = None
    action_required: bool = False


class DashboardAlerts(BaseModel):
    """Schema for dashboard alerts"""
    alerts: List[AlertItem]
    critical_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    info_count: int = Field(..., ge=0)


class PerformanceMetrics(BaseModel):
    """Schema for performance metrics"""
    average_collection_time: float = Field(..., ge=0, description="Average days to collect payment")
    invoice_to_payment_ratio: float = Field(..., ge=0, description="Ratio of payments to invoices")
    customer_retention_rate: float = Field(..., ge=0, le=100, description="Percentage of repeat customers")
    revenue_per_customer: Decimal = Field(..., decimal_places=2)
    monthly_recurring_revenue: Decimal = Field(..., decimal_places=2)


class CashFlowProjection(BaseModel):
    """Schema for cash flow projection"""
    projected_date: date
    expected_inflow: Decimal = Field(..., decimal_places=2)
    expected_outflow: Decimal = Field(..., decimal_places=2)
    net_cash_flow: Decimal = Field(..., decimal_places=2)
    confidence_level: float = Field(..., ge=0, le=100)


class DashboardWidget(BaseModel):
    """Schema for dashboard widget"""
    widget_id: str
    title: str
    type: str = Field(..., pattern="^(metric|chart|table|alert)$")
    data: Dict
    last_updated: datetime
    refresh_interval: Optional[int] = Field(None, description="Refresh interval in seconds")


class CustomDashboard(BaseModel):
    """Schema for custom dashboard configuration"""
    dashboard_id: str
    name: str
    description: Optional[str] = None
    widgets: List[DashboardWidget]
    layout: Dict = Field(..., description="Widget layout configuration")
    is_default: bool = False
    created_at: datetime
    updated_at: datetime


class DashboardExportParams(BaseModel):
    """Schema for dashboard export parameters"""
    format: str = Field("pdf", pattern="^(pdf|excel|csv)$", description="Export format")
    include_charts: bool = Field(True, description="Include charts in export")
    include_tables: bool = Field(True, description="Include data tables")
    date_from: Optional[date] = Field(None, description="Start date for export data")
    date_to: Optional[date] = Field(None, description="End date for export data")


class DashboardComparison(BaseModel):
    """Schema for dashboard period comparison"""
    current_period: DashboardOverview
    previous_period: DashboardOverview
    changes: Dict[str, float] = Field(..., description="Percentage changes between periods")
    insights: List[str] = Field(..., description="Key insights from comparison")


class DashboardGoals(BaseModel):
    """Schema for dashboard goals and targets"""
    revenue_target: Decimal = Field(..., decimal_places=2)
    collection_target: float = Field(..., ge=0, le=100)
    customer_growth_target: int = Field(..., ge=0)
    overdue_limit: Decimal = Field(..., decimal_places=2)
    target_period: str = Field(..., description="Target period (monthly, quarterly, yearly)")


class DashboardProgress(BaseModel):
    """Schema for progress towards goals"""
    goals: DashboardGoals
    current_progress: Dict[str, float] = Field(..., description="Progress percentage towards each goal")
    on_track: Dict[str, bool] = Field(..., description="Whether each goal is on track")
    recommendations: List[str] = Field(..., description="Recommendations to achieve goals")
