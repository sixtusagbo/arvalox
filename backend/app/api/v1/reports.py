from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.aging_report import (
    AgingReport,
    AgingReportParams,
    AgingTrends,
    AgingTrendsParams,
    CustomerAgingSummary,
    OverdueInvoice,
    OverdueInvoicesParams,
)
from app.services.aging_report_service import AgingReportService
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardParams,
    KPISummary,
    QuickStats,
)

router = APIRouter()


@router.get("/aging", response_model=AgingReport)
async def get_aging_report(
    as_of_date: Optional[date] = Query(
        None, description="Date to calculate aging as of (defaults to today)"
    ),
    customer_id: Optional[int] = Query(
        None, gt=0, description="Filter by specific customer"
    ),
    include_paid: bool = Query(
        False, description="Include fully paid invoices"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate comprehensive accounts receivable aging report"""

    aging_service = AgingReportService(db)

    report = await aging_service.generate_aging_report(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
        customer_id=customer_id,
        include_paid=include_paid,
    )

    return AgingReport(**report)


@router.get("/aging/summary", response_model=list[CustomerAgingSummary])
async def get_aging_summary_by_customer(
    as_of_date: Optional[date] = Query(
        None, description="Date to calculate aging as of (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aging summary grouped by customer"""

    aging_service = AgingReportService(db)

    customer_summaries = await aging_service.get_aging_summary_by_customer(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
    )

    return [CustomerAgingSummary(**summary) for summary in customer_summaries]


@router.get("/aging/overdue", response_model=list[OverdueInvoice])
async def get_overdue_invoices(
    days_overdue: int = Query(1, ge=1, description="Minimum days overdue"),
    customer_id: Optional[int] = Query(
        None, gt=0, description="Filter by specific customer"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get invoices that are overdue by specified number of days"""

    aging_service = AgingReportService(db)

    overdue_invoices = await aging_service.get_overdue_invoices(
        organization_id=current_user.organization_id,
        days_overdue=days_overdue,
        customer_id=customer_id,
    )

    return [OverdueInvoice(**invoice) for invoice in overdue_invoices]


@router.get("/aging/trends", response_model=AgingTrends)
async def get_aging_trends(
    months_back: int = Query(
        6, ge=1, le=24, description="Number of months to look back"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aging trends over time"""

    aging_service = AgingReportService(db)

    trends = await aging_service.get_aging_trends(
        organization_id=current_user.organization_id,
        months_back=months_back,
    )

    return AgingTrends(trends=trends, months_back=months_back)


@router.get("/aging/metrics", response_model=dict)
async def get_aging_metrics(
    as_of_date: Optional[date] = Query(
        None, description="Date to calculate metrics as of (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aging metrics and KPIs"""

    aging_service = AgingReportService(db)

    # Get the full aging report
    report = await aging_service.generate_aging_report(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
        include_paid=False,
    )

    # Calculate metrics
    summary = report["summary"]
    total_outstanding = summary["total"]["amount"]
    total_overdue = (
        summary["days_1_30"]["amount"]
        + summary["days_31_60"]["amount"]
        + summary["days_61_90"]["amount"]
        + summary["days_over_90"]["amount"]
    )

    overdue_percentage = (
        float(total_overdue / total_outstanding * 100)
        if total_outstanding > 0
        else 0.0
    )

    # Calculate average days outstanding (weighted by amount)
    total_weighted_days = 0
    total_amount = 0

    for invoice in report["invoice_details"]:
        if invoice["outstanding_amount"] > 0:
            total_weighted_days += invoice["days_overdue"] * float(
                invoice["outstanding_amount"]
            )
            total_amount += float(invoice["outstanding_amount"])

    average_days_outstanding = (
        total_weighted_days / total_amount if total_amount > 0 else 0.0
    )

    # Find worst aging customer
    worst_customer = None
    worst_amount = 0

    for customer in report["customer_summaries"]:
        overdue_amount = (
            customer["days_1_30"]
            + customer["days_31_60"]
            + customer["days_61_90"]
            + customer["days_over_90"]
        )
        if overdue_amount > worst_amount:
            worst_amount = overdue_amount
            worst_customer = customer["customer_name"]

    # Calculate collection efficiency (current vs overdue)
    collection_efficiency = (
        float(summary["current"]["amount"] / total_outstanding * 100)
        if total_outstanding > 0
        else 100.0
    )

    metrics = {
        "total_outstanding": total_outstanding,
        "total_overdue": total_overdue,
        "overdue_percentage": round(overdue_percentage, 2),
        "average_days_outstanding": round(average_days_outstanding, 1),
        "worst_aging_customer": worst_customer,
        "worst_aging_amount": worst_amount,
        "collection_efficiency": round(collection_efficiency, 2),
    }

    return {
        "report_date": report["report_date"],
        "organization_id": report["organization_id"],
        "metrics": metrics,
        "aging_summary": summary,
    }


@router.get("/aging/alerts", response_model=dict)
async def get_aging_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aging-based alerts and warnings"""

    aging_service = AgingReportService(db)

    # Get current aging report
    current_report = await aging_service.generate_aging_report(
        organization_id=current_user.organization_id,
        include_paid=False,
    )

    # Get overdue invoices for alerts
    critical_overdue = await aging_service.get_overdue_invoices(
        organization_id=current_user.organization_id,
        days_overdue=90,
    )

    new_overdue = await aging_service.get_overdue_invoices(
        organization_id=current_user.organization_id,
        days_overdue=1,
    )

    # Calculate alert metrics
    critical_overdue_count = len(critical_overdue)
    critical_overdue_amount = sum(
        inv["outstanding_amount"] for inv in critical_overdue
    )

    new_overdue_count = len(new_overdue)
    new_overdue_amount = sum(inv["outstanding_amount"] for inv in new_overdue)

    # Identify high-risk customers (over 60 days outstanding > $1000)
    collection_risk_customers = []
    total_at_risk_amount = 0

    for customer in current_report["customer_summaries"]:
        high_risk_amount = customer["days_61_90"] + customer["days_over_90"]
        if high_risk_amount > 1000:  # Configurable threshold
            collection_risk_customers.append(customer["customer_name"])
            total_at_risk_amount += high_risk_amount

    alerts = {
        "critical_overdue_count": critical_overdue_count,
        "critical_overdue_amount": critical_overdue_amount,
        "new_overdue_count": new_overdue_count,
        "new_overdue_amount": new_overdue_amount,
        "collection_risk_customers": collection_risk_customers,
        "total_at_risk_amount": total_at_risk_amount,
    }

    return {
        "report_date": current_report["report_date"],
        "organization_id": current_report["organization_id"],
        "alerts": alerts,
    }


@router.get("/aging/dashboard", response_model=dict)
async def get_aging_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive aging dashboard data"""

    aging_service = AgingReportService(db)

    # Get current metrics
    metrics_response = await get_aging_metrics(db=db, current_user=current_user)

    # Get alerts
    alerts_response = await get_aging_alerts(db=db, current_user=current_user)

    # Get recent trends (last 3 months)
    trends_response = await get_aging_trends(
        months_back=3, db=db, current_user=current_user
    )

    # Get top customers by outstanding amount
    customer_summaries = await aging_service.get_aging_summary_by_customer(
        organization_id=current_user.organization_id,
    )

    # Take top 10 customers by total outstanding
    top_customers = sorted(
        customer_summaries, key=lambda x: x["total"], reverse=True
    )[:10]

    return {
        "report_date": metrics_response["report_date"],
        "organization_id": metrics_response["organization_id"],
        "metrics": metrics_response["metrics"],
        "alerts": alerts_response["alerts"],
        "aging_summary": metrics_response["aging_summary"],
        "recent_trends": trends_response.trends,
        "top_customers_by_outstanding": top_customers,
    }


@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard_overview(
    date_from: Optional[date] = Query(
        None, description="Start date for metrics (defaults to 30 days ago)"
    ),
    date_to: Optional[date] = Query(
        None, description="End date for metrics (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive dashboard overview with all KPIs"""

    dashboard_service = DashboardService(db)

    dashboard_data = await dashboard_service.get_dashboard_overview(
        organization_id=current_user.organization_id,
        date_from=date_from,
        date_to=date_to,
    )

    return DashboardOverview(**dashboard_data)


@router.get("/dashboard/kpis", response_model=KPISummary)
async def get_kpi_summary(
    date_from: Optional[date] = Query(
        None, description="Start date for KPIs (defaults to 30 days ago)"
    ),
    date_to: Optional[date] = Query(
        None, description="End date for KPIs (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get key performance indicators summary"""

    dashboard_service = DashboardService(db)

    dashboard_data = await dashboard_service.get_dashboard_overview(
        organization_id=current_user.organization_id,
        date_from=date_from,
        date_to=date_to,
    )

    # Extract KPIs from dashboard data
    revenue_metrics = dashboard_data["revenue_metrics"]
    aging_metrics = dashboard_data["aging_metrics"]
    customer_metrics = dashboard_data["customer_metrics"]
    invoice_metrics = dashboard_data["invoice_metrics"]

    kpis = {
        "total_revenue": revenue_metrics["total_revenue"],
        "outstanding_amount": revenue_metrics["outstanding_amount"],
        "overdue_amount": aging_metrics["total_overdue"],
        "collection_efficiency": aging_metrics["collection_efficiency"],
        "revenue_growth": revenue_metrics["revenue_growth_percentage"],
        "total_customers": customer_metrics["total_customers"],
        "active_invoices": revenue_metrics["invoice_count"],
        "overdue_invoices": invoice_metrics["overdue_count"],
    }

    return KPISummary(**kpis)


@router.get("/dashboard/quick-stats", response_model=QuickStats)
async def get_quick_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get quick dashboard statistics"""

    dashboard_service = DashboardService(db)

    # Get current month data
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    dashboard_data = await dashboard_service.get_dashboard_overview(
        organization_id=current_user.organization_id,
        date_from=first_day_of_month,
        date_to=today,
    )

    revenue_metrics = dashboard_data["revenue_metrics"]
    customer_metrics = dashboard_data["customer_metrics"]
    payment_metrics = dashboard_data["payment_metrics"]
    aging_metrics = dashboard_data["aging_metrics"]

    quick_stats = {
        "total_revenue_this_month": revenue_metrics["total_revenue"],
        "total_outstanding": revenue_metrics["outstanding_amount"],
        "overdue_amount": aging_metrics["total_overdue"],
        "total_customers": customer_metrics["total_customers"],
        "invoices_this_month": revenue_metrics["invoice_count"],
        "payments_this_month": payment_metrics["payment_count"],
    }

    return QuickStats(**quick_stats)


@router.get("/dashboard/revenue-metrics", response_model=dict)
async def get_revenue_metrics(
    date_from: Optional[date] = Query(
        None, description="Start date for metrics"
    ),
    date_to: Optional[date] = Query(None, description="End date for metrics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed revenue metrics"""

    dashboard_service = DashboardService(db)

    if not date_to:
        date_to = date.today()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    revenue_metrics = await dashboard_service.get_revenue_metrics(
        organization_id=current_user.organization_id,
        date_from=date_from,
        date_to=date_to,
    )

    return {
        "date_range": {"from": date_from, "to": date_to},
        "metrics": revenue_metrics,
    }


@router.get("/dashboard/top-customers", response_model=list)
async def get_top_customers(
    limit: int = Query(
        10, ge=1, le=50, description="Number of top customers to return"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get top customers by revenue"""

    dashboard_service = DashboardService(db)

    top_customers = await dashboard_service.get_top_customers(
        organization_id=current_user.organization_id,
        limit=limit,
    )

    return top_customers


@router.get("/dashboard/recent-activity", response_model=list)
async def get_recent_activity(
    limit: int = Query(
        20, ge=1, le=100, description="Number of recent activities to return"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent activity across invoices and payments"""

    dashboard_service = DashboardService(db)

    recent_activity = await dashboard_service.get_recent_activity(
        organization_id=current_user.organization_id,
        limit=limit,
    )

    return recent_activity
