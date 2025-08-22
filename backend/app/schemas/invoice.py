from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class InvoiceCustomer(BaseModel):
    """Minimal customer schema for invoice responses"""

    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    customer_code: str


class InvoiceItemBase(BaseModel):
    """Base invoice item schema"""

    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=2)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating invoice items"""

    pass


class InvoiceItemUpdate(BaseModel):
    """Schema for updating invoice items"""

    description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    unit_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class InvoiceItemResponse(InvoiceItemBase):
    """Schema for invoice item response"""

    model_config = {"from_attributes": True}

    id: int
    invoice_id: int
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    @field_validator("line_total", mode="before")
    @classmethod
    def calculate_line_total(cls, v, info):
        if info.data and "quantity" in info.data and "unit_price" in info.data:
            return info.data["quantity"] * info.data["unit_price"]
        return v


class InvoiceBase(BaseModel):
    """Base invoice schema"""

    invoice_number: str = Field(..., min_length=1, max_length=50)
    customer_id: int = Field(..., gt=0)
    invoice_date: date
    due_date: date
    status: str = Field(
        "draft", pattern="^(draft|sent|paid|overdue|cancelled)$"
    )
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_after_invoice_date(cls, v, info):
        if (
            info.data
            and "invoice_date" in info.data
            and v < info.data["invoice_date"]
        ):
            raise ValueError("Due date must be after invoice date")
        return v


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices"""

    items: List[InvoiceItemCreate] = Field(..., min_length=1)

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Invoice must have at least one item")
        return v


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices"""

    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    customer_id: Optional[int] = Field(None, gt=0)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(
        None, pattern="^(draft|sent|paid|overdue|cancelled)$"
    )
    notes: Optional[str] = Field(None, max_length=1000)
    items: Optional[List[InvoiceItemCreate]] = None

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_after_invoice_date(cls, v, info):
        if (
            v
            and info.data
            and "invoice_date" in info.data
            and info.data["invoice_date"]
            and v < info.data["invoice_date"]
        ):
            raise ValueError("Due date must be after invoice date")
        return v


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response"""

    model_config = {"from_attributes": True}

    id: int
    organization_id: int
    user_id: int
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    items: List[InvoiceItemResponse] = []
    customer: Optional[InvoiceCustomer] = None
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "subtotal", "tax_amount", "total_amount", "paid_amount", mode="before"
    )
    @classmethod
    def convert_decimal(cls, v):
        if v is None:
            return Decimal("0.00")
        return Decimal(str(v))


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list response"""

    invoices: List[InvoiceResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class InvoiceSearchParams(BaseModel):
    """Schema for invoice search and filtering parameters"""

    search: Optional[str] = Field(
        None, description="Search in invoice_number, customer name, notes"
    )
    status: Optional[str] = Field(
        None,
        pattern="^(draft|sent|paid|overdue|cancelled)$",
        description="Filter by status",
    )
    customer_id: Optional[int] = Field(
        None, gt=0, description="Filter by customer"
    )
    date_from: Optional[date] = Field(
        None, description="Filter invoices from this date"
    )
    date_to: Optional[date] = Field(
        None, description="Filter invoices to this date"
    )
    amount_min: Optional[Decimal] = Field(
        None, ge=0, description="Minimum total amount"
    )
    amount_max: Optional[Decimal] = Field(
        None, ge=0, description="Maximum total amount"
    )
    overdue_only: Optional[bool] = Field(
        None, description="Show only overdue invoices"
    )
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("invoice_date", description="Sort field")
    sort_order: Optional[str] = Field(
        "desc", pattern="^(asc|desc)$", description="Sort order"
    )

    @field_validator("date_to")
    @classmethod
    def date_to_must_be_after_date_from(cls, v, info):
        if (
            v
            and info.data
            and "date_from" in info.data
            and info.data["date_from"]
            and v < info.data["date_from"]
        ):
            raise ValueError("End date must be after start date")
        return v

    @field_validator("amount_max")
    @classmethod
    def amount_max_must_be_greater_than_min(cls, v, info):
        if (
            v
            and info.data
            and "amount_min" in info.data
            and info.data["amount_min"]
            and v < info.data["amount_min"]
        ):
            raise ValueError(
                "Maximum amount must be greater than minimum amount"
            )
        return v


class InvoiceStatusUpdate(BaseModel):
    """Schema for updating invoice status"""

    status: str = Field(..., pattern="^(draft|sent|paid|overdue|cancelled)$")


class InvoiceSummary(BaseModel):
    """Schema for invoice summary statistics"""

    total_invoices: int
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    overdue_count: int
    overdue_amount: Decimal
    draft_count: int
    sent_count: int
    paid_count: int


class InvoiceNumberGeneration(BaseModel):
    """Schema for invoice number generation"""

    prefix: Optional[str] = Field("INV", max_length=10)
    year: Optional[int] = Field(None, ge=2020, le=2100)
    sequence_length: Optional[int] = Field(4, ge=3, le=10)
    separator: Optional[str] = Field("-", max_length=3)
