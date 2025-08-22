from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate,
    PaymentListResponse,
    PaymentResponse,
    PaymentSearchParams,
    PaymentStatusUpdate,
    PaymentSummary,
    PaymentUpdate,
    InvoicePaymentSummary,
    PaymentAllocationCreate,
)
from app.services.payment_allocation_service import PaymentAllocationService
from app.services.payment_history_service import PaymentHistoryService

router = APIRouter()


@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new payment"""

    # Check if invoice exists and belongs to the organization
    invoice = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.id == payment_data.invoice_id,
                Invoice.organization_id == current_user.organization_id,
            )
        )
    )
    invoice = invoice.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check if reference number already exists for this organization (if provided)
    if payment_data.reference_number:
        existing_payment = await db.execute(
            select(Payment).where(
                and_(
                    Payment.organization_id == current_user.organization_id,
                    Payment.reference_number == payment_data.reference_number,
                )
            )
        )
        if existing_payment.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Payment reference number already exists in your organization",
            )

    # Validate payment amount doesn't exceed outstanding balance
    outstanding_balance = invoice.total_amount - invoice.paid_amount
    if payment_data.amount > outstanding_balance:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount (${payment_data.amount}) exceeds outstanding balance (${outstanding_balance})",
        )

    # Create payment
    payment = Payment(
        organization_id=current_user.organization_id,
        invoice_id=payment_data.invoice_id,
        user_id=current_user.id,
        payment_date=payment_data.payment_date,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        reference_number=payment_data.reference_number,
        notes=payment_data.notes,
        status="completed",
    )

    db.add(payment)

    # Update invoice paid amount
    invoice.paid_amount += payment_data.amount

    await db.commit()
    await db.refresh(payment)

    # Manually serialize payment with invoice data to avoid MissingGreenlet error
    payment_dict = {
        "id": payment.id,
        "organization_id": payment.organization_id,
        "invoice_id": payment.invoice_id,
        "user_id": payment.user_id,
        "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "status": payment.status,
        "notes": payment.notes,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "customer_name": invoice.customer.name if invoice.customer else None,
            "total_amount": float(invoice.total_amount)
        }
    }

    return payment_dict


@router.get("/", response_model=PaymentListResponse)
async def list_payments(
    search: Optional[str] = Query(
        None, description="Search in reference_number, notes"
    ),
    invoice_id: Optional[int] = Query(
        None, gt=0, description="Filter by invoice"
    ),
    payment_method: Optional[str] = Query(
        None,
        pattern="^(cash|check|bank_transfer|credit_card|online)$",
        description="Filter by payment method",
    ),
    status: Optional[str] = Query(
        None,
        pattern="^(completed|pending|failed|cancelled)$",
        description="Filter by status",
    ),
    date_from: Optional[date] = Query(
        None, description="Filter payments from this date"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter payments to this date"
    ),
    amount_min: Optional[Decimal] = Query(
        None, ge=0, description="Minimum payment amount"
    ),
    amount_max: Optional[Decimal] = Query(
        None, ge=0, description="Maximum payment amount"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("payment_date", description="Sort field"),
    sort_order: Optional[str] = Query(
        "desc", pattern="^(asc|desc)$", description="Sort order"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List payments with search and filtering"""

    # Base query with organization filtering and invoice relationship
    query = select(Payment).options(selectinload(Payment.invoice)).where(
        Payment.organization_id == current_user.organization_id
    )

    # Apply search filter
    if search:
        search_filter = or_(
            Payment.reference_number.ilike(f"%{search}%"),
            Payment.notes.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    # Apply filters
    if invoice_id:
        query = query.where(Payment.invoice_id == invoice_id)

    if payment_method:
        query = query.where(Payment.payment_method == payment_method)

    if status:
        query = query.where(Payment.status == status)

    if date_from:
        query = query.where(Payment.payment_date >= date_from)
    if date_to:
        query = query.where(Payment.payment_date <= date_to)

    if amount_min is not None:
        query = query.where(Payment.amount >= amount_min)
    if amount_max is not None:
        query = query.where(Payment.amount <= amount_max)

    # Apply sorting
    sort_column = getattr(Payment, sort_by, Payment.payment_date)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    payments = result.scalars().all()

    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page

    # Manually serialize payments with invoice data to avoid MissingGreenlet error
    payments_data = []
    for payment in payments:
        payment_dict = {
            "id": payment.id,
            "organization_id": payment.organization_id,
            "invoice_id": payment.invoice_id,
            "user_id": payment.user_id,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "amount": float(payment.amount),
            "payment_method": payment.payment_method,
            "reference_number": payment.reference_number,
            "status": payment.status,
            "notes": payment.notes,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
            "invoice": None
        }
        
        # Add invoice data if available
        if payment.invoice:
            payment_dict["invoice"] = {
                "id": payment.invoice.id,
                "invoice_number": payment.invoice.invoice_number,
                "customer_name": payment.invoice.customer.name if payment.invoice.customer else None,
                "total_amount": float(payment.invoice.total_amount)
            }
        
        payments_data.append(payment_dict)

    return PaymentListResponse(
        payments=payments_data,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific payment by ID"""

    payment = await db.execute(
        select(Payment).options(selectinload(Payment.invoice)).where(
            and_(
                Payment.id == payment_id,
                Payment.organization_id == current_user.organization_id,
            )
        )
    )
    payment = payment.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Manually serialize payment with invoice data to avoid MissingGreenlet error
    payment_dict = {
        "id": payment.id,
        "organization_id": payment.organization_id,
        "invoice_id": payment.invoice_id,
        "user_id": payment.user_id,
        "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "status": payment.status,
        "notes": payment.notes,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
        "invoice": None
    }
    
    # Add invoice data if available
    if payment.invoice:
        payment_dict["invoice"] = {
            "id": payment.invoice.id,
            "invoice_number": payment.invoice.invoice_number,
            "customer_name": payment.invoice.customer.name if payment.invoice.customer else None,
            "total_amount": float(payment.invoice.total_amount)
        }

    return payment_dict


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a payment"""

    # Get existing payment
    payment = await db.execute(
        select(Payment).where(
            and_(
                Payment.id == payment_id,
                Payment.organization_id == current_user.organization_id,
            )
        )
    )
    payment = payment.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check if payment can be updated (only pending and failed payments)
    if payment.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot update completed or cancelled payments",
        )

    # Check if reference number is being updated and already exists
    if (
        payment_data.reference_number
        and payment_data.reference_number != payment.reference_number
    ):
        existing_payment = await db.execute(
            select(Payment).where(
                and_(
                    Payment.organization_id == current_user.organization_id,
                    Payment.reference_number == payment_data.reference_number,
                    Payment.id != payment_id,
                )
            )
        )
        if existing_payment.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Payment reference number already exists in your organization",
            )

    # If amount is being updated, validate against invoice balance
    if payment_data.amount and payment_data.amount != payment.amount:
        # Get invoice to check outstanding balance
        invoice = await db.execute(
            select(Invoice).where(Invoice.id == payment.invoice_id)
        )
        invoice = invoice.scalar_one()

        # Calculate new outstanding balance (removing current payment, adding new amount)
        current_outstanding = (
            invoice.total_amount - invoice.paid_amount + payment.amount
        )
        if payment_data.amount > current_outstanding:
            raise HTTPException(
                status_code=400,
                detail=f"Payment amount (${payment_data.amount}) exceeds outstanding balance (${current_outstanding})",
            )

        # Update invoice paid amount
        invoice.paid_amount = (
            invoice.paid_amount - payment.amount + payment_data.amount
        )

    # Update payment fields
    update_data = payment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    await db.commit()
    await db.refresh(payment)

    return payment


@router.patch("/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: int,
    status_data: PaymentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update payment status"""

    payment = await db.execute(
        select(Payment).where(
            and_(
                Payment.id == payment_id,
                Payment.organization_id == current_user.organization_id,
            )
        )
    )
    payment = payment.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Validate status transitions
    valid_transitions = {
        "pending": ["completed", "failed", "cancelled"],
        "completed": [
            "cancelled"
        ],  # Only allow cancellation of completed payments
        "failed": ["pending", "completed", "cancelled"],
        "cancelled": [],  # Cancelled payments cannot change status
    }

    if status_data.status not in valid_transitions.get(payment.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from {payment.status} to {status_data.status}",
        )

    # If changing from completed to cancelled, update invoice paid amount
    if payment.status == "completed" and status_data.status == "cancelled":
        invoice = await db.execute(
            select(Invoice).where(Invoice.id == payment.invoice_id)
        )
        invoice = invoice.scalar_one()
        invoice.paid_amount -= payment.amount

    # If changing to completed from other status, update invoice paid amount
    elif payment.status != "completed" and status_data.status == "completed":
        invoice = await db.execute(
            select(Invoice).where(Invoice.id == payment.invoice_id)
        )
        invoice = invoice.scalar_one()
        invoice.paid_amount += payment.amount

    payment.status = status_data.status
    await db.commit()
    await db.refresh(payment)

    return payment


@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a payment (only pending and failed payments can be deleted)"""

    payment = await db.execute(
        select(Payment).where(
            and_(
                Payment.id == payment_id,
                Payment.organization_id == current_user.organization_id,
            )
        )
    )
    payment = payment.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Only allow deletion of pending and failed payments
    if payment.status not in ["pending", "failed"]:
        raise HTTPException(
            status_code=400,
            detail="Only pending and failed payments can be deleted",
        )

    await db.delete(payment)
    await db.commit()

    return {"message": "Payment deleted successfully"}


@router.get("/summary/stats", response_model=PaymentSummary)
async def get_payment_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment summary statistics"""

    # Get all payments for the organization
    result = await db.execute(
        select(Payment).where(
            Payment.organization_id == current_user.organization_id
        )
    )
    payments = result.scalars().all()

    # Calculate statistics
    total_payments = len(payments)
    total_amount = sum(payment.amount for payment in payments)

    # Count by status
    status_counts = {}
    status_amounts = {}
    for payment in payments:
        status_counts[payment.status] = status_counts.get(payment.status, 0) + 1
        status_amounts[payment.status] = (
            status_amounts.get(payment.status, Decimal("0")) + payment.amount
        )

    return PaymentSummary(
        total_payments=total_payments,
        total_amount=total_amount,
        completed_payments=status_counts.get("completed", 0),
        completed_amount=status_amounts.get("completed", Decimal("0")),
        pending_payments=status_counts.get("pending", 0),
        pending_amount=status_amounts.get("pending", Decimal("0")),
        failed_payments=status_counts.get("failed", 0),
        failed_amount=status_amounts.get("failed", Decimal("0")),
    )


@router.get(
    "/invoice/{invoice_id}/summary", response_model=InvoicePaymentSummary
)
async def get_invoice_payment_summary(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment summary for a specific invoice"""

    # Check if invoice exists and belongs to the organization
    invoice = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.organization_id == current_user.organization_id,
            )
        )
    )
    invoice = invoice.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get payments for this invoice
    payments_result = await db.execute(
        select(Payment)
        .where(
            and_(
                Payment.invoice_id == invoice_id,
                Payment.organization_id == current_user.organization_id,
                Payment.status == "completed",
            )
        )
        .order_by(desc(Payment.payment_date))
    )
    payments = payments_result.scalars().all()

    # Calculate summary
    paid_amount = sum(payment.amount for payment in payments)
    outstanding_amount = invoice.total_amount - paid_amount
    payment_count = len(payments)
    last_payment_date = payments[0].payment_date if payments else None

    return InvoicePaymentSummary(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        total_amount=invoice.total_amount,
        paid_amount=paid_amount,
        outstanding_amount=outstanding_amount,
        payment_count=payment_count,
        last_payment_date=last_payment_date,
    )


@router.post("/allocate", response_model=dict)
async def allocate_payment(
    payment_data: PaymentAllocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allocate a payment across multiple invoices"""

    allocation_service = PaymentAllocationService(db)

    try:
        payment, allocation_details = await allocation_service.allocate_payment(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            payment_data=payment_data,
        )

        return {
            "message": "Payment allocated successfully",
            "primary_payment_id": payment.id,
            "total_amount": payment_data.amount,
            "allocations": allocation_details,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auto-allocate", response_model=dict)
async def auto_allocate_payment(
    payment_amount: Decimal = Query(..., gt=0, description="Payment amount"),
    payment_method: str = Query(
        ..., pattern="^(cash|check|bank_transfer|credit_card|online)$"
    ),
    payment_date: date = Query(..., description="Payment date"),
    reference_number: Optional[str] = Query(
        None, description="Reference number"
    ),
    notes: Optional[str] = Query(None, description="Payment notes"),
    customer_id: Optional[int] = Query(
        None, gt=0, description="Limit to specific customer"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Automatically allocate a payment to outstanding invoices"""

    allocation_service = PaymentAllocationService(db)

    try:
        (
            payments,
            allocation_details,
        ) = await allocation_service.auto_allocate_payment(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            payment_amount=payment_amount,
            payment_method=payment_method,
            payment_date=payment_date,
            reference_number=reference_number,
            notes=notes,
            customer_id=customer_id,
        )

        return {
            "message": "Payment auto-allocated successfully",
            "payment_count": len(payments),
            "total_amount": payment_amount,
            "allocations": allocation_details,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/allocation-suggestions", response_model=dict)
async def get_allocation_suggestions(
    payment_amount: Decimal = Query(..., gt=0, description="Payment amount"),
    customer_id: Optional[int] = Query(
        None, gt=0, description="Limit to specific customer"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get suggested allocation for a payment amount"""

    allocation_service = PaymentAllocationService(db)

    suggestions = await allocation_service.get_allocation_suggestions(
        organization_id=current_user.organization_id,
        payment_amount=payment_amount,
        customer_id=customer_id,
    )

    return {
        "payment_amount": payment_amount,
        "suggestions": suggestions,
        "total_suggested": sum(
            s.get("suggested_allocation", 0) for s in suggestions
        ),
    }


@router.get("/history", response_model=dict)
async def get_payment_history(
    customer_id: Optional[int] = Query(
        None, gt=0, description="Filter by customer"
    ),
    invoice_id: Optional[int] = Query(
        None, gt=0, description="Filter by invoice"
    ),
    user_id: Optional[int] = Query(
        None, gt=0, description="Filter by user who recorded payment"
    ),
    date_from: Optional[date] = Query(
        None, description="Filter from this date"
    ),
    date_to: Optional[date] = Query(None, description="Filter to this date"),
    payment_method: Optional[str] = Query(
        None, pattern="^(cash|check|bank_transfer|credit_card|online)$"
    ),
    status: Optional[str] = Query(
        None, pattern="^(completed|pending|failed|cancelled)$"
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum records to return"
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive payment history with filtering"""

    history_service = PaymentHistoryService(db)

    payment_history, total = await history_service.get_payment_history(
        organization_id=current_user.organization_id,
        customer_id=customer_id,
        invoice_id=invoice_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        payment_method=payment_method,
        status=status,
        limit=limit,
        offset=offset,
    )

    return {
        "payment_history": payment_history,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": total > (offset + limit),
    }


@router.get("/history/customer/{customer_id}", response_model=dict)
async def get_customer_payment_history(
    customer_id: int,
    limit: int = Query(
        50, ge=1, le=100, description="Maximum records to return"
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment history for a specific customer with summary"""

    history_service = PaymentHistoryService(db)

    (
        payment_history,
        customer_summary,
    ) = await history_service.get_customer_payment_history(
        organization_id=current_user.organization_id,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )

    return {
        "customer_summary": customer_summary,
        "payment_history": payment_history,
        "limit": limit,
        "offset": offset,
        "has_more": customer_summary["payment_history_count"]
        > (offset + limit),
    }


@router.get("/audit/{payment_id}", response_model=dict)
async def get_payment_audit_trail(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed audit trail for a specific payment"""

    history_service = PaymentHistoryService(db)

    audit_trail = await history_service.get_payment_audit_trail(
        organization_id=current_user.organization_id,
        payment_id=payment_id,
    )

    if not audit_trail:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {"audit_trail": audit_trail}


@router.get("/analytics/trends", response_model=dict)
async def get_payment_trends(
    period: str = Query(
        "monthly",
        pattern="^(daily|weekly|monthly|quarterly)$",
        description="Aggregation period",
    ),
    date_from: Optional[date] = Query(
        None, description="Start date for trends"
    ),
    date_to: Optional[date] = Query(None, description="End date for trends"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment trends over time"""

    history_service = PaymentHistoryService(db)

    trends = await history_service.get_payment_trends(
        organization_id=current_user.organization_id,
        period=period,
        date_from=date_from,
        date_to=date_to,
    )

    return {
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "trends": trends,
    }


@router.get("/analytics/payment-methods", response_model=dict)
async def get_payment_method_analytics(
    date_from: Optional[date] = Query(
        None, description="Start date for analytics"
    ),
    date_to: Optional[date] = Query(None, description="End date for analytics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment method analytics"""

    history_service = PaymentHistoryService(db)

    analytics = await history_service.get_payment_method_analytics(
        organization_id=current_user.organization_id,
        date_from=date_from,
        date_to=date_to,
    )

    return {
        "date_from": date_from,
        "date_to": date_to,
        "payment_methods": analytics,
    }
