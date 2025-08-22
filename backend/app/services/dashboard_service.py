from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.organization import Organization
from app.models.payment import Payment
from app.services.aging_report_service import AgingReportService


class DashboardService:
    """Service for generating dashboard metrics and KPIs"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.aging_service = AgingReportService(db)

    async def get_dashboard_overview(
        self,
        organization_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict:
        """
        Get comprehensive dashboard overview with all KPIs
        
        Args:
            organization_id: Organization ID for multi-tenant filtering
            date_from: Optional start date for metrics (defaults to 30 days ago)
            date_to: Optional end date for metrics (defaults to today)
            
        Returns:
            Complete dashboard overview with all metrics
        """
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        # Get all dashboard components
        revenue_metrics = await self.get_revenue_metrics(organization_id, date_from, date_to)
        invoice_metrics = await self.get_invoice_metrics(organization_id, date_from, date_to)
        payment_metrics = await self.get_payment_metrics(organization_id, date_from, date_to)
        customer_metrics = await self.get_customer_metrics(organization_id)
        aging_metrics = await self.get_aging_metrics(organization_id)
        recent_activity = await self.get_recent_activity(organization_id, limit=10)
        top_customers = await self.get_top_customers(organization_id, limit=5)

        return {
            "organization_id": organization_id,
            "date_range": {
                "from": date_from,
                "to": date_to,
            },
            "revenue_metrics": revenue_metrics,
            "invoice_metrics": invoice_metrics,
            "payment_metrics": payment_metrics,
            "customer_metrics": customer_metrics,
            "aging_metrics": aging_metrics,
            "recent_activity": recent_activity,
            "top_customers": top_customers,
            "generated_at": datetime.now(),
        }

    async def get_revenue_metrics(
        self,
        organization_id: int,
        date_from: date,
        date_to: date,
    ) -> Dict:
        """Get revenue-related metrics"""
        
        # Total revenue (completed invoices)
        revenue_query = (
            select(
                func.sum(Invoice.total_amount).label("total_revenue"),
                func.count(Invoice.id).label("invoice_count"),
                func.avg(Invoice.total_amount).label("average_invoice_value"),
            )
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.status.in_(["sent", "paid", "overdue"]),
                    Invoice.invoice_date >= date_from,
                    Invoice.invoice_date <= date_to,
                )
            )
        )
        
        revenue_result = await self.db.execute(revenue_query)
        revenue_row = revenue_result.first()
        
        # Outstanding revenue
        outstanding_query = (
            select(
                func.sum(Invoice.total_amount - Invoice.paid_amount).label("outstanding_amount"),
                func.count(Invoice.id).label("outstanding_count"),
            )
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.total_amount > Invoice.paid_amount,
                    Invoice.status.in_(["sent", "overdue"]),
                )
            )
        )
        
        outstanding_result = await self.db.execute(outstanding_query)
        outstanding_row = outstanding_result.first()
        
        # Previous period comparison (same period length, previous period)
        period_length = (date_to - date_from).days
        prev_date_to = date_from - timedelta(days=1)
        prev_date_from = prev_date_to - timedelta(days=period_length)
        
        prev_revenue_query = (
            select(func.sum(Invoice.total_amount).label("prev_revenue"))
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.status.in_(["sent", "paid", "overdue"]),
                    Invoice.invoice_date >= prev_date_from,
                    Invoice.invoice_date <= prev_date_to,
                )
            )
        )
        
        prev_revenue_result = await self.db.execute(prev_revenue_query)
        prev_revenue = prev_revenue_result.scalar() or Decimal('0.00')
        
        # Calculate growth
        current_revenue = revenue_row.total_revenue or Decimal('0.00')
        revenue_growth = 0.0
        if prev_revenue > 0:
            revenue_growth = float((current_revenue - prev_revenue) / prev_revenue * 100)

        return {
            "total_revenue": current_revenue,
            "invoice_count": revenue_row.invoice_count or 0,
            "average_invoice_value": revenue_row.average_invoice_value or Decimal('0.00'),
            "outstanding_amount": outstanding_row.outstanding_amount or Decimal('0.00'),
            "outstanding_count": outstanding_row.outstanding_count or 0,
            "revenue_growth_percentage": round(revenue_growth, 2),
            "previous_period_revenue": prev_revenue,
        }

    async def get_invoice_metrics(
        self,
        organization_id: int,
        date_from: date,
        date_to: date,
    ) -> Dict:
        """Get invoice-related metrics"""
        
        # Invoice status breakdown
        status_query = (
            select(
                Invoice.status,
                func.count(Invoice.id).label("count"),
                func.sum(Invoice.total_amount).label("amount"),
            )
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.invoice_date >= date_from,
                    Invoice.invoice_date <= date_to,
                )
            )
            .group_by(Invoice.status)
        )
        
        status_result = await self.db.execute(status_query)
        status_breakdown = {}
        
        for row in status_result:
            status_breakdown[row.status] = {
                "count": row.count,
                "amount": row.amount or Decimal('0.00'),
            }
        
        # Overdue invoices
        overdue_query = (
            select(
                func.count(Invoice.id).label("overdue_count"),
                func.sum(Invoice.total_amount - Invoice.paid_amount).label("overdue_amount"),
            )
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.due_date < date.today(),
                    Invoice.total_amount > Invoice.paid_amount,
                    Invoice.status.in_(["sent", "overdue"]),
                )
            )
        )
        
        overdue_result = await self.db.execute(overdue_query)
        overdue_row = overdue_result.first()

        return {
            "status_breakdown": status_breakdown,
            "overdue_count": overdue_row.overdue_count or 0,
            "overdue_amount": overdue_row.overdue_amount or Decimal('0.00'),
        }

    async def get_payment_metrics(
        self,
        organization_id: int,
        date_from: date,
        date_to: date,
    ) -> Dict:
        """Get payment-related metrics"""
        
        # Payment summary
        payment_query = (
            select(
                func.count(Payment.id).label("payment_count"),
                func.sum(Payment.amount).label("total_payments"),
                func.avg(Payment.amount).label("average_payment"),
            )
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.payment_date >= date_from,
                    Payment.payment_date <= date_to,
                    Payment.status == "completed",
                )
            )
        )
        
        payment_result = await self.db.execute(payment_query)
        payment_row = payment_result.first()
        
        # Payment method breakdown
        method_query = (
            select(
                Payment.payment_method,
                func.count(Payment.id).label("count"),
                func.sum(Payment.amount).label("amount"),
            )
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.payment_date >= date_from,
                    Payment.payment_date <= date_to,
                    Payment.status == "completed",
                )
            )
            .group_by(Payment.payment_method)
        )
        
        method_result = await self.db.execute(method_query)
        method_breakdown = {}
        
        for row in method_result:
            method_breakdown[row.payment_method] = {
                "count": row.count,
                "amount": row.amount or Decimal('0.00'),
            }

        return {
            "payment_count": payment_row.payment_count or 0,
            "total_payments": payment_row.total_payments or Decimal('0.00'),
            "average_payment": payment_row.average_payment or Decimal('0.00'),
            "method_breakdown": method_breakdown,
        }

    async def get_customer_metrics(self, organization_id: int) -> Dict:
        """Get customer-related metrics"""
        
        # Customer summary
        customer_query = (
            select(
                func.count(Customer.id).label("total_customers"),
                func.count(Customer.id).filter(Customer.status == "active").label("active_customers"),
                func.count(Customer.id).filter(Customer.status == "inactive").label("inactive_customers"),
            )
            .where(Customer.organization_id == organization_id)
        )
        
        customer_result = await self.db.execute(customer_query)
        customer_row = customer_result.first()
        
        # Customers with outstanding balances
        outstanding_customers_query = (
            select(func.count(func.distinct(Invoice.customer_id)).label("customers_with_outstanding"))
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.total_amount > Invoice.paid_amount,
                    Invoice.status.in_(["sent", "overdue"]),
                )
            )
        )
        
        outstanding_customers_result = await self.db.execute(outstanding_customers_query)
        customers_with_outstanding = outstanding_customers_result.scalar() or 0

        return {
            "total_customers": customer_row.total_customers or 0,
            "active_customers": customer_row.active_customers or 0,
            "inactive_customers": customer_row.inactive_customers or 0,
            "customers_with_outstanding": customers_with_outstanding,
        }

    async def get_aging_metrics(self, organization_id: int) -> Dict:
        """Get aging-related metrics from aging service"""
        
        aging_report = await self.aging_service.generate_aging_report(
            organization_id=organization_id,
            include_paid=False,
        )
        
        summary = aging_report["summary"]
        total_outstanding = summary["total"]["amount"]
        total_overdue = (
            summary["days_1_30"]["amount"] +
            summary["days_31_60"]["amount"] +
            summary["days_61_90"]["amount"] +
            summary["days_over_90"]["amount"]
        )
        
        overdue_percentage = float(total_overdue / total_outstanding * 100) if total_outstanding > 0 else 0.0
        collection_efficiency = float(summary["current"]["amount"] / total_outstanding * 100) if total_outstanding > 0 else 100.0

        return {
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "overdue_percentage": round(overdue_percentage, 2),
            "collection_efficiency": round(collection_efficiency, 2),
            "aging_breakdown": summary,
        }

    async def get_recent_activity(
        self,
        organization_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        """Get recent activity across invoices and payments"""
        
        activities = []
        
        # Recent invoices
        recent_invoices_query = (
            select(Invoice)
            .where(Invoice.organization_id == organization_id)
            .order_by(desc(Invoice.created_at))
            .limit(limit // 2)
        )
        
        recent_invoices_result = await self.db.execute(recent_invoices_query)
        recent_invoices = recent_invoices_result.scalars().all()
        
        for invoice in recent_invoices:
            activities.append({
                "type": "invoice",
                "id": invoice.id,
                "description": f"Invoice {invoice.invoice_number} created",
                "amount": invoice.total_amount,
                "date": invoice.created_at,
                "status": invoice.status,
            })
        
        # Recent payments
        recent_payments_query = (
            select(Payment)
            .where(Payment.organization_id == organization_id)
            .order_by(desc(Payment.created_at))
            .limit(limit // 2)
        )
        
        recent_payments_result = await self.db.execute(recent_payments_query)
        recent_payments = recent_payments_result.scalars().all()
        
        for payment in recent_payments:
            activities.append({
                "type": "payment",
                "id": payment.id,
                "description": f"Payment received: {payment.payment_method}",
                "amount": payment.amount,
                "date": payment.created_at,
                "status": payment.status,
            })
        
        # Sort by date (most recent first)
        activities.sort(key=lambda x: x["date"], reverse=True)
        
        return activities[:limit]

    async def get_top_customers(
        self,
        organization_id: int,
        limit: int = 5,
    ) -> List[Dict]:
        """Get top customers by revenue"""
        
        top_customers_query = (
            select(
                Customer.id,
                Customer.name,
                Organization.name.label("company_name"),
                func.sum(Invoice.total_amount).label("total_revenue"),
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.total_amount - Invoice.paid_amount).label("outstanding_amount"),
            )
            .join(Invoice, Customer.id == Invoice.customer_id)
            .join(Organization, Customer.organization_id == Organization.id)
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Invoice.status.in_(["sent", "paid", "overdue"]),
                )
            )
            .group_by(Customer.id, Customer.name, Organization.name)
            .order_by(desc("total_revenue"))
            .limit(limit)
        )
        
        top_customers_result = await self.db.execute(top_customers_query)
        top_customers = []
        
        for row in top_customers_result:
            top_customers.append({
                "customer_id": row.id,
                "contact_name": row.name,
                "company_name": row.company_name,
                "total_revenue": row.total_revenue or Decimal('0.00'),
                "invoice_count": row.invoice_count or 0,
                "outstanding_amount": row.outstanding_amount or Decimal('0.00'),
            })
        
        return top_customers
