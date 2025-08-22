from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import User


class PaymentHistoryService:
    """Service for payment history tracking and audit trails"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_payment_history(
        self,
        organization_id: int,
        customer_id: Optional[int] = None,
        invoice_id: Optional[int] = None,
        user_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        payment_method: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """
        Get comprehensive payment history with related data
        
        Args:
            organization_id: Organization ID for multi-tenant filtering
            customer_id: Optional customer filter
            invoice_id: Optional invoice filter
            user_id: Optional user filter (who recorded the payment)
            date_from: Optional start date filter
            date_to: Optional end date filter
            payment_method: Optional payment method filter
            status: Optional status filter
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Tuple of (payment history list, total count)
        """
        # Build base query with joins
        query = (
            select(Payment)
            .options(
                selectinload(Payment.invoice).selectinload(Invoice.customer).selectinload(Customer.organization),
                selectinload(Payment.user),
            )
            .where(Payment.organization_id == organization_id)
        )
        
        # Apply filters
        if customer_id:
            query = query.join(Invoice).where(Invoice.customer_id == customer_id)
        
        if invoice_id:
            query = query.where(Payment.invoice_id == invoice_id)
        
        if user_id:
            query = query.where(Payment.user_id == user_id)
        
        if date_from:
            query = query.where(Payment.payment_date >= date_from)
        
        if date_to:
            query = query.where(Payment.payment_date <= date_to)
        
        if payment_method:
            query = query.where(Payment.payment_method == payment_method)
        
        if status:
            query = query.where(Payment.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply ordering and pagination
        query = query.order_by(desc(Payment.payment_date), desc(Payment.created_at))
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        payments = result.scalars().all()
        
        # Format payment history
        payment_history = []
        for payment in payments:
            history_item = {
                "payment_id": payment.id,
                "payment_date": payment.payment_date,
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "reference_number": payment.reference_number,
                "status": payment.status,
                "notes": payment.notes,
                "created_at": payment.created_at,
                "updated_at": payment.updated_at,
                "invoice": {
                    "id": payment.invoice.id if payment.invoice else None,
                    "invoice_number": payment.invoice.invoice_number if payment.invoice else None,
                    "total_amount": payment.invoice.total_amount if payment.invoice else None,
                    "customer": {
                        "id": payment.invoice.customer.id if payment.invoice and payment.invoice.customer else None,
                        "contact_name": payment.invoice.customer.name if payment.invoice and payment.invoice.customer else None,
                        "company_name": payment.invoice.customer.organization.name if payment.invoice and payment.invoice.customer else None,
                    } if payment.invoice and payment.invoice.customer else None,
                } if payment.invoice else None,
                "recorded_by": {
                    "id": payment.user.id if payment.user else None,
                    "email": payment.user.email if payment.user else None,
                } if payment.user else None,
            }
            payment_history.append(history_item)
        
        return payment_history, total

    async def get_customer_payment_history(
        self,
        organization_id: int,
        customer_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict], Dict]:
        """
        Get payment history for a specific customer with summary
        
        Args:
            organization_id: Organization ID
            customer_id: Customer ID
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            Tuple of (payment history, customer payment summary)
        """
        # Get customer payment history
        payment_history, total = await self.get_payment_history(
            organization_id=organization_id,
            customer_id=customer_id,
            limit=limit,
            offset=offset,
        )
        
        # Get customer payment summary
        summary_query = (
            select(
                func.count(Payment.id).label("total_payments"),
                func.sum(Payment.amount).label("total_amount"),
                func.count(Payment.id).filter(Payment.status == "completed").label("completed_payments"),
                func.sum(Payment.amount).filter(Payment.status == "completed").label("completed_amount"),
                func.max(Payment.payment_date).label("last_payment_date"),
                func.min(Payment.payment_date).label("first_payment_date"),
            )
            .select_from(Payment)
            .join(Invoice)
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Invoice.customer_id == customer_id,
                )
            )
        )
        
        summary_result = await self.db.execute(summary_query)
        summary_row = summary_result.first()
        
        customer_summary = {
            "customer_id": customer_id,
            "total_payments": summary_row.total_payments or 0,
            "total_amount": summary_row.total_amount or Decimal('0.00'),
            "completed_payments": summary_row.completed_payments or 0,
            "completed_amount": summary_row.completed_amount or Decimal('0.00'),
            "last_payment_date": summary_row.last_payment_date,
            "first_payment_date": summary_row.first_payment_date,
            "payment_history_count": total,
        }
        
        return payment_history, customer_summary

    async def get_payment_audit_trail(
        self,
        organization_id: int,
        payment_id: int,
    ) -> Dict:
        """
        Get detailed audit trail for a specific payment
        
        Args:
            organization_id: Organization ID
            payment_id: Payment ID
            
        Returns:
            Payment audit trail with all related information
        """
        # Get payment with all related data
        query = (
            select(Payment)
            .options(
                selectinload(Payment.invoice).selectinload(Invoice.customer).selectinload(Customer.organization),
                selectinload(Payment.invoice).selectinload(Invoice.items),
                selectinload(Payment.user),
            )
            .where(
                and_(
                    Payment.id == payment_id,
                    Payment.organization_id == organization_id,
                )
            )
        )
        
        result = await self.db.execute(query)
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        # Build comprehensive audit trail
        audit_trail = {
            "payment": {
                "id": payment.id,
                "payment_date": payment.payment_date,
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "reference_number": payment.reference_number,
                "status": payment.status,
                "notes": payment.notes,
                "created_at": payment.created_at,
                "updated_at": payment.updated_at,
            },
            "invoice": {
                "id": payment.invoice.id if payment.invoice else None,
                "invoice_number": payment.invoice.invoice_number if payment.invoice else None,
                "invoice_date": payment.invoice.invoice_date if payment.invoice else None,
                "due_date": payment.invoice.due_date if payment.invoice else None,
                "total_amount": payment.invoice.total_amount if payment.invoice else None,
                "paid_amount": payment.invoice.paid_amount if payment.invoice else None,
                "status": payment.invoice.status if payment.invoice else None,
                "line_items_count": len(payment.invoice.items) if payment.invoice and payment.invoice.items else 0,
            } if payment.invoice else None,
            "customer": {
                "id": payment.invoice.customer.id if payment.invoice and payment.invoice.customer else None,
                "contact_name": payment.invoice.customer.name if payment.invoice and payment.invoice.customer else None,
                "company_name": payment.invoice.customer.organization.name if payment.invoice and payment.invoice.customer else None,
                "email": payment.invoice.customer.email if payment.invoice and payment.invoice.customer else None,
            } if payment.invoice and payment.invoice.customer else None,
            "recorded_by": {
                "id": payment.user.id if payment.user else None,
                "email": payment.user.email if payment.user else None,
                "role": payment.user.role if payment.user else None,
            } if payment.user else None,
            "organization_id": payment.organization_id,
        }
        
        return audit_trail

    async def get_payment_trends(
        self,
        organization_id: int,
        period: str = "monthly",  # daily, weekly, monthly, quarterly
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """
        Get payment trends over time
        
        Args:
            organization_id: Organization ID
            period: Aggregation period (daily, weekly, monthly, quarterly)
            date_from: Optional start date
            date_to: Optional end date
            
        Returns:
            List of payment trend data
        """
        # Set default date range if not provided
        if not date_to:
            date_to = date.today()
        if not date_from:
            if period == "daily":
                date_from = date_to - timedelta(days=30)
            elif period == "weekly":
                date_from = date_to - timedelta(weeks=12)
            elif period == "monthly":
                date_from = date_to - timedelta(days=365)
            else:  # quarterly
                date_from = date_to - timedelta(days=730)
        
        # Build date truncation based on period
        if period == "daily":
            date_trunc = func.date(Payment.payment_date)
            date_format = "YYYY-MM-DD"
        elif period == "weekly":
            date_trunc = func.date_trunc('week', Payment.payment_date)
            date_format = "YYYY-\"W\"WW"
        elif period == "monthly":
            date_trunc = func.date_trunc('month', Payment.payment_date)
            date_format = "YYYY-MM"
        else:  # quarterly
            date_trunc = func.date_trunc('quarter', Payment.payment_date)
            date_format = "YYYY-\"Q\"Q"
        
        # Build trends query
        trends_query = (
            select(
                date_trunc.label("period"),
                func.count(Payment.id).label("payment_count"),
                func.sum(Payment.amount).label("total_amount"),
                func.avg(Payment.amount).label("average_amount"),
                func.count(Payment.id).filter(Payment.status == "completed").label("completed_count"),
                func.sum(Payment.amount).filter(Payment.status == "completed").label("completed_amount"),
            )
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.payment_date >= date_from,
                    Payment.payment_date <= date_to,
                )
            )
            .group_by(date_trunc)
            .order_by(date_trunc)
        )
        
        result = await self.db.execute(trends_query)
        trends_data = []
        
        for row in result:
            trends_data.append({
                "period": row.period.strftime("%Y-%m-%d") if row.period else None,
                "payment_count": row.payment_count or 0,
                "total_amount": row.total_amount or Decimal('0.00'),
                "average_amount": row.average_amount or Decimal('0.00'),
                "completed_count": row.completed_count or 0,
                "completed_amount": row.completed_amount or Decimal('0.00'),
            })
        
        return trends_data

    async def get_payment_method_analytics(
        self,
        organization_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """
        Get payment method analytics
        
        Args:
            organization_id: Organization ID
            date_from: Optional start date
            date_to: Optional end date
            
        Returns:
            List of payment method statistics
        """
        # Build query
        query = (
            select(
                Payment.payment_method,
                func.count(Payment.id).label("count"),
                func.sum(Payment.amount).label("total_amount"),
                func.avg(Payment.amount).label("average_amount"),
            )
            .where(Payment.organization_id == organization_id)
        )
        
        if date_from:
            query = query.where(Payment.payment_date >= date_from)
        if date_to:
            query = query.where(Payment.payment_date <= date_to)
        
        query = query.group_by(Payment.payment_method).order_by(desc("total_amount"))
        
        result = await self.db.execute(query)
        analytics = []
        
        total_amount = Decimal('0.00')
        for row in result:
            total_amount += row.total_amount or Decimal('0.00')
        
        for row in result:
            amount = row.total_amount or Decimal('0.00')
            percentage = float(amount / total_amount * 100) if total_amount > 0 else 0.0
            
            analytics.append({
                "payment_method": row.payment_method,
                "count": row.count or 0,
                "total_amount": amount,
                "average_amount": row.average_amount or Decimal('0.00'),
                "percentage": round(percentage, 2),
            })
        
        return analytics
