from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.invoice import Invoice


class AgingReportService:
    """Service for generating accounts receivable aging reports"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_aging_report(
        self,
        organization_id: int,
        as_of_date: Optional[date] = None,
        customer_id: Optional[int] = None,
        include_paid: bool = False,
    ) -> Dict:
        """
        Generate comprehensive accounts receivable aging report

        Args:
            organization_id: Organization ID for multi-tenant filtering
            as_of_date: Date to calculate aging as of (defaults to today)
            customer_id: Optional customer filter
            include_paid: Whether to include fully paid invoices

        Returns:
            Comprehensive aging report with summary and details
        """
        if not as_of_date:
            as_of_date = date.today()

        # Get outstanding invoices
        invoices = await self._get_outstanding_invoices(
            organization_id, customer_id, include_paid
        )

        # Calculate aging for each invoice
        aging_details = []
        aging_summary = {
            "current": {"count": 0, "amount": Decimal("0.00")},
            "days_1_30": {"count": 0, "amount": Decimal("0.00")},
            "days_31_60": {"count": 0, "amount": Decimal("0.00")},
            "days_61_90": {"count": 0, "amount": Decimal("0.00")},
            "days_over_90": {"count": 0, "amount": Decimal("0.00")},
            "total": {"count": 0, "amount": Decimal("0.00")},
        }

        customer_summaries = {}

        for invoice in invoices:
            outstanding_amount = invoice.total_amount - invoice.paid_amount

            # Skip if no outstanding amount and not including paid
            if outstanding_amount <= 0 and not include_paid:
                continue

            # Calculate days overdue
            days_overdue = (as_of_date - invoice.due_date).days

            # Determine aging bucket
            aging_bucket = self._get_aging_bucket(days_overdue)

            # Add to aging summary
            aging_summary[aging_bucket]["count"] += 1
            aging_summary[aging_bucket]["amount"] += outstanding_amount
            aging_summary["total"]["count"] += 1
            aging_summary["total"]["amount"] += outstanding_amount

            # Customer summary
            customer_key = invoice.customer_id
            if customer_key not in customer_summaries:
                customer_summaries[customer_key] = {
                    "customer_id": invoice.customer_id,
                    "customer_name": invoice.customer.name
                    if invoice.customer
                    else "Unknown",
                    "company_name": invoice.customer.organization.name
                    if invoice.customer
                    else None,
                    "current": Decimal("0.00"),
                    "days_1_30": Decimal("0.00"),
                    "days_31_60": Decimal("0.00"),
                    "days_61_90": Decimal("0.00"),
                    "days_over_90": Decimal("0.00"),
                    "total": Decimal("0.00"),
                    "invoice_count": 0,
                }

            customer_summaries[customer_key][aging_bucket] += outstanding_amount
            customer_summaries[customer_key]["total"] += outstanding_amount
            customer_summaries[customer_key]["invoice_count"] += 1

            # Invoice detail
            aging_details.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "customer_name": invoice.customer.name
                    if invoice.customer
                    else "Unknown",
                    "company_name": invoice.customer.organization.name
                    if invoice.customer
                    else None,
                    "invoice_date": invoice.invoice_date,
                    "due_date": invoice.due_date,
                    "total_amount": invoice.total_amount,
                    "paid_amount": invoice.paid_amount,
                    "outstanding_amount": outstanding_amount,
                    "days_overdue": days_overdue,
                    "aging_bucket": aging_bucket,
                    "status": invoice.status,
                }
            )

        # Sort details by days overdue (most overdue first)
        aging_details.sort(key=lambda x: x["days_overdue"], reverse=True)

        # Convert customer summaries to list and sort by total outstanding
        customer_list = list(customer_summaries.values())
        customer_list.sort(key=lambda x: x["total"], reverse=True)

        return {
            "report_date": as_of_date,
            "organization_id": organization_id,
            "customer_filter": customer_id,
            "include_paid": include_paid,
            "summary": aging_summary,
            "customer_summaries": customer_list,
            "invoice_details": aging_details,
            "total_customers": len(customer_list),
            "total_invoices": len(aging_details),
        }

    async def get_aging_summary_by_customer(
        self,
        organization_id: int,
        as_of_date: Optional[date] = None,
    ) -> List[Dict]:
        """
        Get aging summary grouped by customer

        Args:
            organization_id: Organization ID
            as_of_date: Date to calculate aging as of

        Returns:
            List of customer aging summaries
        """
        report = await self.generate_aging_report(
            organization_id=organization_id,
            as_of_date=as_of_date,
            include_paid=False,
        )

        return report["customer_summaries"]

    async def get_overdue_invoices(
        self,
        organization_id: int,
        days_overdue: int = 1,
        customer_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get invoices that are overdue by specified number of days

        Args:
            organization_id: Organization ID
            days_overdue: Minimum days overdue (default: 1)
            customer_id: Optional customer filter

        Returns:
            List of overdue invoices
        """
        cutoff_date = date.today() - timedelta(days=days_overdue)

        query = (
            select(Invoice)
            .options(selectinload(Invoice.customer).selectinload(Customer.organization))
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.due_date <= cutoff_date,
                    Invoice.total_amount > Invoice.paid_amount,
                    Invoice.status.in_(["sent", "overdue"]),
                )
            )
        )

        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)

        query = query.order_by(Invoice.due_date.asc())

        result = await self.db.execute(query)
        invoices = result.scalars().all()

        overdue_list = []
        for invoice in invoices:
            days_past_due = (date.today() - invoice.due_date).days
            outstanding_amount = invoice.total_amount - invoice.paid_amount

            overdue_list.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "customer_name": invoice.customer.name
                    if invoice.customer
                    else "Unknown",
                    "company_name": invoice.customer.organization.name
                    if invoice.customer
                    else None,
                    "invoice_date": invoice.invoice_date,
                    "due_date": invoice.due_date,
                    "total_amount": invoice.total_amount,
                    "paid_amount": invoice.paid_amount,
                    "outstanding_amount": outstanding_amount,
                    "days_overdue": days_past_due,
                    "status": invoice.status,
                }
            )

        return overdue_list

    async def get_aging_trends(
        self,
        organization_id: int,
        months_back: int = 6,
    ) -> List[Dict]:
        """
        Get aging trends over time

        Args:
            organization_id: Organization ID
            months_back: Number of months to look back

        Returns:
            List of aging trend data by month
        """
        trends = []
        current_date = date.today()

        for i in range(months_back):
            # Calculate the first day of the month
            if i == 0:
                report_date = current_date
            else:
                # Go back i months
                year = current_date.year
                month = current_date.month - i
                if month <= 0:
                    month += 12
                    year -= 1
                report_date = date(year, month, 1)

            # Generate aging report for this date
            report = await self.generate_aging_report(
                organization_id=organization_id,
                as_of_date=report_date,
                include_paid=False,
            )

            trends.append(
                {
                    "report_date": report_date,
                    "month_year": report_date.strftime("%Y-%m"),
                    "summary": report["summary"],
                    "total_customers": report["total_customers"],
                    "total_invoices": report["total_invoices"],
                }
            )

        # Sort by date (most recent first)
        trends.sort(key=lambda x: x["report_date"], reverse=True)

        return trends

    def _get_aging_bucket(self, days_overdue: int) -> str:
        """
        Determine aging bucket based on days overdue

        Args:
            days_overdue: Number of days overdue

        Returns:
            Aging bucket name
        """
        if days_overdue <= 0:
            return "current"
        elif days_overdue <= 30:
            return "days_1_30"
        elif days_overdue <= 60:
            return "days_31_60"
        elif days_overdue <= 90:
            return "days_61_90"
        else:
            return "days_over_90"

    async def _get_outstanding_invoices(
        self,
        organization_id: int,
        customer_id: Optional[int] = None,
        include_paid: bool = False,
    ) -> List[Invoice]:
        """
        Get outstanding invoices for aging calculation

        Args:
            organization_id: Organization ID
            customer_id: Optional customer filter
            include_paid: Whether to include fully paid invoices

        Returns:
            List of invoices for aging calculation
        """
        query = (
            select(Invoice)
            .options(selectinload(Invoice.customer).selectinload(Customer.organization))
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.status.in_(["sent", "overdue", "paid"]),
                )
            )
        )

        if not include_paid:
            query = query.where(Invoice.total_amount > Invoice.paid_amount)

        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)

        query = query.order_by(Invoice.due_date.asc())

        result = await self.db.execute(query)
        return result.scalars().all()
