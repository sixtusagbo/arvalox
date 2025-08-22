from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from app.models.organization import Organization
from app.models.user import User
from app.services.pdf_service import InvoicePDFService
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceSearchParams,
    InvoiceStatusUpdate,
    InvoiceSummary,
    InvoiceUpdate,
)

router = APIRouter()


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new invoice"""

    # Check if customer exists and belongs to the organization
    customer = await db.execute(
        select(Customer).where(
            and_(
                Customer.id == invoice_data.customer_id,
                Customer.organization_id == current_user.organization_id,
            )
        )
    )
    customer = customer.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Check if invoice number already exists for this organization
    existing_invoice = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.organization_id == current_user.organization_id,
                Invoice.invoice_number == invoice_data.invoice_number,
            )
        )
    )
    if existing_invoice.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Invoice number already exists in your organization",
        )

    # Calculate totals
    subtotal = sum(
        item.quantity * item.unit_price for item in invoice_data.items
    )
    tax_amount = Decimal("0.00")  # TODO: Implement tax calculation
    total_amount = subtotal + tax_amount

    # Create invoice
    invoice = Invoice(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        invoice_number=invoice_data.invoice_number,
        customer_id=invoice_data.customer_id,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status=invoice_data.status,
        notes=invoice_data.notes,
    )

    db.add(invoice)
    await db.flush()  # Get the invoice ID

    # Create invoice items
    for item_data in invoice_data.items:
        line_total = item_data.quantity * item_data.unit_price
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            line_total=line_total,
        )
        db.add(invoice_item)

    await db.commit()
    await db.refresh(invoice)

    # Load the invoice with items
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.id == invoice.id)
    )
    invoice_with_items = result.scalar_one()

    return invoice_with_items


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    search: Optional[str] = Query(
        None, description="Search in invoice_number, customer name, notes"
    ),
    status: Optional[str] = Query(
        None,
        pattern="^(draft|sent|paid|overdue|cancelled)$",
        description="Filter by status",
    ),
    customer_id: Optional[int] = Query(
        None, gt=0, description="Filter by customer"
    ),
    date_from: Optional[date] = Query(
        None, description="Filter invoices from this date"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter invoices to this date"
    ),
    amount_min: Optional[Decimal] = Query(
        None, ge=0, description="Minimum total amount"
    ),
    amount_max: Optional[Decimal] = Query(
        None, ge=0, description="Maximum total amount"
    ),
    overdue_only: Optional[bool] = Query(
        None, description="Show only overdue invoices"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("invoice_date", description="Sort field"),
    sort_order: Optional[str] = Query(
        "desc", pattern="^(asc|desc)$", description="Sort order"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List invoices with search and filtering"""

    # Base query with organization filtering
    query = (
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.organization_id == current_user.organization_id)
    )

    # Apply search filter
    if search:
        # Join with customer for name search
        query = query.join(Customer)
        search_filter = or_(
            Invoice.invoice_number.ilike(f"%{search}%"),
            Customer.name.ilike(f"%{search}%"),
            Invoice.notes.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    # Apply status filter
    if status:
        query = query.where(Invoice.status == status)

    # Apply customer filter
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)

    # Apply date filters
    if date_from:
        query = query.where(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.where(Invoice.invoice_date <= date_to)

    # Apply amount filters
    if amount_min is not None:
        query = query.where(Invoice.total_amount >= amount_min)
    if amount_max is not None:
        query = query.where(Invoice.total_amount <= amount_max)

    # Apply overdue filter
    if overdue_only:
        today = date.today()
        query = query.where(
            and_(
                Invoice.due_date < today,
                Invoice.status.in_(["sent", "overdue"]),
            )
        )

    # Apply sorting
    sort_column = getattr(Invoice, sort_by, Invoice.invoice_date)
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
    invoices = result.scalars().all()

    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page

    return InvoiceListResponse(
        invoices=invoices,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific invoice by ID"""

    invoice = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.customer)
        )
        .where(
            and_(
                Invoice.id == invoice_id,
                Invoice.organization_id == current_user.organization_id,
            )
        )
    )
    invoice = invoice.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an invoice"""

    # Get existing invoice
    invoice = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(
            and_(
                Invoice.id == invoice_id,
                Invoice.organization_id == current_user.organization_id,
            )
        )
    )
    invoice = invoice.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check if invoice can be updated (only draft and sent invoices)
    if invoice.status in ["paid", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot update paid or cancelled invoices",
        )

    # Check if customer exists (if being updated)
    if invoice_data.customer_id:
        customer = await db.execute(
            select(Customer).where(
                and_(
                    Customer.id == invoice_data.customer_id,
                    Customer.organization_id == current_user.organization_id,
                )
            )
        )
        if not customer.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Customer not found")

    # Check if invoice number is being updated and already exists
    if (
        invoice_data.invoice_number
        and invoice_data.invoice_number != invoice.invoice_number
    ):
        existing_invoice = await db.execute(
            select(Invoice).where(
                and_(
                    Invoice.organization_id == current_user.organization_id,
                    Invoice.invoice_number == invoice_data.invoice_number,
                    Invoice.id != invoice_id,
                )
            )
        )
        if existing_invoice.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Invoice number already exists in your organization",
            )

    # Update invoice fields
    update_data = invoice_data.model_dump(exclude_unset=True, exclude={"items"})
    for field, value in update_data.items():
        setattr(invoice, field, value)

    # Update items if provided
    if invoice_data.items is not None:
        # Delete existing items
        await db.execute(
            InvoiceItem.__table__.delete().where(
                InvoiceItem.invoice_id == invoice_id
            )
        )

        # Create new items
        subtotal = Decimal("0.00")
        for item_data in invoice_data.items:
            line_total = item_data.quantity * item_data.unit_price
            subtotal += line_total
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                line_total=line_total,
            )
            db.add(invoice_item)

        # Update totals
        tax_amount = Decimal("0.00")  # TODO: Implement tax calculation
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = subtotal + tax_amount

    await db.commit()
    await db.refresh(invoice)

    # Load the updated invoice with items
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.id == invoice.id)
    )
    updated_invoice = result.scalar_one()

    return updated_invoice


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(
    invoice_id: int,
    status_data: InvoiceStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update invoice status"""

    invoice = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(
            and_(
                Invoice.id == invoice_id,
                Invoice.organization_id == current_user.organization_id,
            )
        )
    )
    invoice = invoice.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Validate status transitions
    valid_transitions = {
        "draft": ["sent", "cancelled"],
        "sent": ["paid", "overdue", "cancelled"],
        "overdue": ["paid", "cancelled"],
        "paid": [],  # Paid invoices cannot change status
        "cancelled": [],  # Cancelled invoices cannot change status
    }

    if status_data.status not in valid_transitions.get(invoice.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from {invoice.status} to {status_data.status}",
        )

    invoice.status = status_data.status
    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an invoice (only draft invoices can be deleted)"""

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

    # Only allow deletion of draft invoices
    if invoice.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft invoices can be deleted",
        )

    await db.delete(invoice)
    await db.commit()

    return {"message": "Invoice deleted successfully"}


@router.get("/summary/stats", response_model=InvoiceSummary)
async def get_invoice_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get invoice summary statistics"""

    # Get all invoices for the organization
    result = await db.execute(
        select(Invoice).where(
            Invoice.organization_id == current_user.organization_id
        )
    )
    invoices = result.scalars().all()

    # Calculate statistics
    total_invoices = len(invoices)
    total_amount = sum(invoice.total_amount for invoice in invoices)
    paid_amount = sum(invoice.paid_amount for invoice in invoices)
    outstanding_amount = total_amount - paid_amount

    # Count by status
    status_counts = {}
    for invoice in invoices:
        status_counts[invoice.status] = status_counts.get(invoice.status, 0) + 1

    # Calculate overdue
    today = date.today()
    overdue_invoices = [
        invoice
        for invoice in invoices
        if invoice.due_date < today and invoice.status in ["sent", "overdue"]
    ]
    overdue_count = len(overdue_invoices)
    overdue_amount = sum(
        invoice.total_amount - invoice.paid_amount
        for invoice in overdue_invoices
    )

    return InvoiceSummary(
        total_invoices=total_invoices,
        total_amount=total_amount,
        paid_amount=paid_amount,
        outstanding_amount=outstanding_amount,
        overdue_count=overdue_count,
        overdue_amount=overdue_amount,
        draft_count=status_counts.get("draft", 0),
        sent_count=status_counts.get("sent", 0),
        paid_count=status_counts.get("paid", 0),
    )


@router.post("/generate-number")
async def generate_invoice_number(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate next invoice number for the organization"""

    # Get the latest invoice number for this organization
    result = await db.execute(
        select(Invoice.invoice_number)
        .where(Invoice.organization_id == current_user.organization_id)
        .order_by(desc(Invoice.created_at))
        .limit(1)
    )
    latest_number = result.scalar_one_or_none()

    # Generate next number
    current_year = datetime.now().year
    prefix = "INV"

    if latest_number:
        # Extract sequence number from latest invoice
        try:
            # Assuming format: INV-YYYY-NNNN
            parts = latest_number.split("-")
            if len(parts) >= 3 and parts[1] == str(current_year):
                sequence = int(parts[2]) + 1
            else:
                sequence = 1
        except (ValueError, IndexError):
            sequence = 1
    else:
        sequence = 1

    next_number = f"{prefix}-{current_year}-{sequence:04d}"

    return {"invoice_number": next_number}


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download invoice as PDF"""

    # Get invoice with items and customer
    invoice_query = (
        select(Invoice)
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.customer),
        )
        .where(
            and_(
                Invoice.id == invoice_id,
                Invoice.organization_id == current_user.organization_id,
            )
        )
    )

    result = await db.execute(invoice_query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get organization
    org_result = await db.execute(
        select(Organization).where(
            Organization.id == current_user.organization_id
        )
    )
    organization = org_result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Prepare customer data
    customer_data = {
        "name": invoice.customer.name,
        "billing_address": invoice.customer.billing_address,
        "email": invoice.customer.email,
        "phone": invoice.customer.phone,
    }

    # Generate PDF
    pdf_service = InvoicePDFService()
    pdf_content = pdf_service.generate_invoice_pdf(
        invoice=invoice, organization=organization, customer_data=customer_data
    )

    # Return PDF response
    filename = f"invoice_{invoice.invoice_number}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/pdf",
        },
    )
