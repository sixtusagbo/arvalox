from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PaymentBase(BaseModel):
    """Base payment schema"""
    payment_date: date
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Payment amount")
    payment_method: str = Field(..., pattern="^(cash|check|bank_transfer|credit_card|online)$")
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class PaymentCreate(PaymentBase):
    """Schema for creating payments"""
    invoice_id: int = Field(..., gt=0)

    @field_validator('payment_date')
    @classmethod
    def validate_payment_date(cls, v):
        if v > date.today():
            raise ValueError('Payment date cannot be in the future')
        return v


class PaymentUpdate(BaseModel):
    """Schema for updating payments"""
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    payment_method: Optional[str] = Field(None, pattern="^(cash|check|bank_transfer|credit_card|online)$")
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(completed|pending|failed|cancelled)$")

    @field_validator('payment_date')
    @classmethod
    def validate_payment_date(cls, v):
        if v and v > date.today():
            raise ValueError('Payment date cannot be in the future')
        return v


class PaymentResponse(PaymentBase):
    """Schema for payment response"""
    model_config = {"from_attributes": True}
    
    id: int
    organization_id: int
    invoice_id: int
    user_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator('amount', mode='before')
    @classmethod
    def convert_decimal(cls, v):
        if v is None:
            return Decimal('0.00')
        return Decimal(str(v))


class PaymentListResponse(BaseModel):
    """Schema for paginated payment list response"""
    payments: List[PaymentResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class PaymentSearchParams(BaseModel):
    """Schema for payment search and filtering parameters"""
    search: Optional[str] = Field(None, description="Search in reference_number, notes")
    invoice_id: Optional[int] = Field(None, gt=0, description="Filter by invoice")
    payment_method: Optional[str] = Field(None, pattern="^(cash|check|bank_transfer|credit_card|online)$", description="Filter by payment method")
    status: Optional[str] = Field(None, pattern="^(completed|pending|failed|cancelled)$", description="Filter by status")
    date_from: Optional[date] = Field(None, description="Filter payments from this date")
    date_to: Optional[date] = Field(None, description="Filter payments to this date")
    amount_min: Optional[Decimal] = Field(None, ge=0, description="Minimum payment amount")
    amount_max: Optional[Decimal] = Field(None, ge=0, description="Maximum payment amount")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("payment_date", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")

    @field_validator('date_to')
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

    @field_validator('amount_max')
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


class PaymentStatusUpdate(BaseModel):
    """Schema for updating payment status"""
    status: str = Field(..., pattern="^(completed|pending|failed|cancelled)$")


class PaymentSummary(BaseModel):
    """Schema for payment summary statistics"""
    total_payments: int
    total_amount: Decimal
    completed_payments: int
    completed_amount: Decimal
    pending_payments: int
    pending_amount: Decimal
    failed_payments: int
    failed_amount: Decimal


class InvoicePaymentSummary(BaseModel):
    """Schema for invoice payment summary"""
    invoice_id: int
    invoice_number: str
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    payment_count: int
    last_payment_date: Optional[date]


class PaymentAllocation(BaseModel):
    """Schema for payment allocation across invoices"""
    invoice_id: int
    allocated_amount: Decimal = Field(..., gt=0, decimal_places=2)

    @field_validator('allocated_amount')
    @classmethod
    def validate_allocated_amount(cls, v):
        if v <= 0:
            raise ValueError('Allocated amount must be greater than zero')
        return v


class PaymentAllocationCreate(BaseModel):
    """Schema for creating payment with allocation"""
    payment_date: date
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str = Field(..., pattern="^(cash|check|bank_transfer|credit_card|online)$")
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    allocations: List[PaymentAllocation] = Field(..., min_length=1)

    @field_validator('payment_date')
    @classmethod
    def validate_payment_date(cls, v):
        if v > date.today():
            raise ValueError('Payment date cannot be in the future')
        return v

    @field_validator('allocations')
    @classmethod
    def validate_allocations(cls, v, info):
        if not v:
            raise ValueError('At least one allocation is required')
        
        # Check that total allocated amount doesn't exceed payment amount
        if info.data and 'amount' in info.data:
            total_allocated = sum(allocation.allocated_amount for allocation in v)
            if total_allocated > info.data['amount']:
                raise ValueError('Total allocated amount cannot exceed payment amount')
        
        return v


class PaymentMethodStats(BaseModel):
    """Schema for payment method statistics"""
    payment_method: str
    count: int
    total_amount: Decimal
    percentage: float


class PaymentTrend(BaseModel):
    """Schema for payment trend data"""
    period: str  # e.g., "2024-01", "2024-Q1"
    payment_count: int
    total_amount: Decimal
    average_amount: Decimal
