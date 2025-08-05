from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.payment import PaymentAllocation, PaymentAllocationCreate


class PaymentAllocationService:
    """Service for handling payment allocation across multiple invoices"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def allocate_payment(
        self,
        organization_id: int,
        user_id: int,
        payment_data: PaymentAllocationCreate,
    ) -> Tuple[Payment, List[Dict]]:
        """
        Allocate a payment across multiple invoices
        
        Args:
            organization_id: Organization ID for multi-tenant isolation
            user_id: User ID who is creating the payment
            payment_data: Payment allocation data
            
        Returns:
            Tuple of (Payment object, List of allocation details)
        """
        # Validate all invoices exist and belong to organization
        invoice_ids = [allocation.invoice_id for allocation in payment_data.allocations]
        invoices = await self._get_invoices(organization_id, invoice_ids)
        
        if len(invoices) != len(invoice_ids):
            raise ValueError("One or more invoices not found")
        
        # Validate allocations don't exceed outstanding balances
        allocation_errors = await self._validate_allocations(invoices, payment_data.allocations)
        if allocation_errors:
            raise ValueError(f"Allocation errors: {allocation_errors}")
        
        # Create the main payment record (we'll use the first invoice as primary)
        primary_invoice = invoices[0]
        primary_allocation = payment_data.allocations[0]
        
        payment = Payment(
            organization_id=organization_id,
            invoice_id=primary_invoice.id,
            user_id=user_id,
            payment_date=payment_data.payment_date,
            amount=primary_allocation.allocated_amount,
            payment_method=payment_data.payment_method,
            reference_number=payment_data.reference_number,
            notes=payment_data.notes,
            status="completed",
        )
        
        self.db.add(payment)
        await self.db.flush()  # Get payment ID
        
        # Create additional payment records for other invoices
        additional_payments = []
        allocation_details = []
        
        # Process primary allocation
        primary_invoice.paid_amount += primary_allocation.allocated_amount
        allocation_details.append({
            "invoice_id": primary_invoice.id,
            "invoice_number": primary_invoice.invoice_number,
            "allocated_amount": primary_allocation.allocated_amount,
            "payment_id": payment.id,
        })
        
        # Process additional allocations
        for allocation in payment_data.allocations[1:]:
            invoice = next(inv for inv in invoices if inv.id == allocation.invoice_id)
            
            # Create additional payment record
            additional_payment = Payment(
                organization_id=organization_id,
                invoice_id=invoice.id,
                user_id=user_id,
                payment_date=payment_data.payment_date,
                amount=allocation.allocated_amount,
                payment_method=payment_data.payment_method,
                reference_number=f"{payment_data.reference_number}-{allocation.invoice_id}",
                notes=f"Allocated from payment {payment_data.reference_number}",
                status="completed",
            )
            
            self.db.add(additional_payment)
            additional_payments.append(additional_payment)
            
            # Update invoice paid amount
            invoice.paid_amount += allocation.allocated_amount
            
            allocation_details.append({
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "allocated_amount": allocation.allocated_amount,
                "payment_id": additional_payment.id,
            })
        
        await self.db.commit()
        
        return payment, allocation_details

    async def auto_allocate_payment(
        self,
        organization_id: int,
        user_id: int,
        payment_amount: Decimal,
        payment_method: str,
        payment_date,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        customer_id: Optional[int] = None,
    ) -> Tuple[List[Payment], List[Dict]]:
        """
        Automatically allocate a payment to outstanding invoices
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            payment_amount: Total payment amount
            payment_method: Payment method
            payment_date: Payment date
            reference_number: Optional reference number
            notes: Optional notes
            customer_id: Optional customer ID to limit allocation to specific customer
            
        Returns:
            Tuple of (List of Payment objects, List of allocation details)
        """
        # Get outstanding invoices ordered by due date (oldest first)
        outstanding_invoices = await self._get_outstanding_invoices(
            organization_id, customer_id
        )
        
        if not outstanding_invoices:
            raise ValueError("No outstanding invoices found for allocation")
        
        # Allocate payment across invoices
        remaining_amount = payment_amount
        payments = []
        allocation_details = []
        
        for invoice in outstanding_invoices:
            if remaining_amount <= 0:
                break
            
            outstanding_balance = invoice.total_amount - invoice.paid_amount
            allocation_amount = min(remaining_amount, outstanding_balance)
            
            # Create payment record
            payment = Payment(
                organization_id=organization_id,
                invoice_id=invoice.id,
                user_id=user_id,
                payment_date=payment_date,
                amount=allocation_amount,
                payment_method=payment_method,
                reference_number=reference_number or f"AUTO-{invoice.invoice_number}",
                notes=notes or f"Auto-allocated payment",
                status="completed",
            )
            
            self.db.add(payment)
            payments.append(payment)
            
            # Update invoice paid amount
            invoice.paid_amount += allocation_amount
            remaining_amount -= allocation_amount
            
            allocation_details.append({
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "allocated_amount": allocation_amount,
                "outstanding_before": outstanding_balance,
                "outstanding_after": outstanding_balance - allocation_amount,
            })
        
        # Handle overpayment
        if remaining_amount > 0:
            # Create a credit payment (negative invoice_id indicates credit)
            credit_payment = Payment(
                organization_id=organization_id,
                invoice_id=None,  # No specific invoice for credit
                user_id=user_id,
                payment_date=payment_date,
                amount=remaining_amount,
                payment_method=payment_method,
                reference_number=f"{reference_number or 'CREDIT'}-OVERPAYMENT",
                notes=f"Overpayment credit: ${remaining_amount}",
                status="completed",
            )
            
            self.db.add(credit_payment)
            payments.append(credit_payment)
            
            allocation_details.append({
                "invoice_id": None,
                "invoice_number": "CREDIT",
                "allocated_amount": remaining_amount,
                "outstanding_before": Decimal('0.00'),
                "outstanding_after": Decimal('0.00'),
                "is_credit": True,
            })
        
        await self.db.commit()
        
        return payments, allocation_details

    async def get_allocation_suggestions(
        self,
        organization_id: int,
        payment_amount: Decimal,
        customer_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get suggested allocation for a payment amount
        
        Args:
            organization_id: Organization ID
            payment_amount: Payment amount to allocate
            customer_id: Optional customer ID to limit suggestions
            
        Returns:
            List of allocation suggestions
        """
        outstanding_invoices = await self._get_outstanding_invoices(
            organization_id, customer_id
        )
        
        suggestions = []
        remaining_amount = payment_amount
        
        for invoice in outstanding_invoices:
            if remaining_amount <= 0:
                break
            
            outstanding_balance = invoice.total_amount - invoice.paid_amount
            suggested_amount = min(remaining_amount, outstanding_balance)
            
            suggestions.append({
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "due_date": invoice.due_date,
                "total_amount": invoice.total_amount,
                "paid_amount": invoice.paid_amount,
                "outstanding_balance": outstanding_balance,
                "suggested_allocation": suggested_amount,
                "days_overdue": (invoice.due_date - payment_amount).days if invoice.due_date < payment_amount else 0,
            })
            
            remaining_amount -= suggested_amount
        
        # Add overpayment info if applicable
        if remaining_amount > 0:
            suggestions.append({
                "invoice_id": None,
                "invoice_number": "OVERPAYMENT",
                "suggested_allocation": remaining_amount,
                "is_overpayment": True,
            })
        
        return suggestions

    async def _get_invoices(
        self, organization_id: int, invoice_ids: List[int]
    ) -> List[Invoice]:
        """Get invoices by IDs for the organization"""
        result = await self.db.execute(
            select(Invoice).where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.id.in_(invoice_ids),
                )
            )
        )
        return result.scalars().all()

    async def _get_outstanding_invoices(
        self, organization_id: int, customer_id: Optional[int] = None
    ) -> List[Invoice]:
        """Get outstanding invoices ordered by due date"""
        query = (
            select(Invoice)
            .where(
                and_(
                    Invoice.organization_id == organization_id,
                    Invoice.total_amount > Invoice.paid_amount,
                    Invoice.status.in_(["sent", "overdue"]),
                )
            )
            .order_by(Invoice.due_date.asc())
        )
        
        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _validate_allocations(
        self, invoices: List[Invoice], allocations: List[PaymentAllocation]
    ) -> List[str]:
        """Validate that allocations don't exceed outstanding balances"""
        errors = []
        
        for allocation in allocations:
            invoice = next(
                (inv for inv in invoices if inv.id == allocation.invoice_id), None
            )
            if not invoice:
                errors.append(f"Invoice {allocation.invoice_id} not found")
                continue
            
            outstanding_balance = invoice.total_amount - invoice.paid_amount
            if allocation.allocated_amount > outstanding_balance:
                errors.append(
                    f"Allocation amount ${allocation.allocated_amount} exceeds "
                    f"outstanding balance ${outstanding_balance} for invoice {invoice.invoice_number}"
                )
        
        return errors
