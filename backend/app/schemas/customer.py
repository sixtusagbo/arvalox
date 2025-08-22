from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerBase(BaseModel):
    """Base customer schema with common fields"""

    customer_code: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    billing_address: Optional[str] = Field(None, max_length=500)
    shipping_address: Optional[str] = Field(None, max_length=500)
    credit_limit: Optional[float] = Field(
        0.0, ge=0, description="Credit limit amount"
    )
    payment_terms: int = Field(
        30, ge=0, le=365, description="Payment terms in days"
    )
    tax_id: Optional[str] = Field(None, max_length=50)
    status: str = Field("active", pattern="^(active|inactive|suspended)$")


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""

    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""

    customer_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    billing_address: Optional[str] = Field(None, max_length=500)
    shipping_address: Optional[str] = Field(None, max_length=500)
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[int] = Field(None, ge=0, le=365)
    tax_id: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")


class CustomerResponse(CustomerBase):
    """Schema for customer response"""

    model_config = {"from_attributes": True}

    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    """Schema for paginated customer list response"""

    customers: list[CustomerResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class CustomerSearchParams(BaseModel):
    """Schema for customer search and filtering parameters"""

    search: Optional[str] = Field(
        None, description="Search in customer_code, name, email, phone"
    )
    status: Optional[str] = Field(
        None,
        pattern="^(active|inactive|suspended)$",
        description="Filter by status",
    )
    payment_terms_min: Optional[int] = Field(
        None, ge=0, description="Minimum payment terms"
    )
    payment_terms_max: Optional[int] = Field(
        None, ge=0, description="Maximum payment terms"
    )
    has_credit_limit: Optional[bool] = Field(
        None, description="Filter customers with credit limit"
    )
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("name", description="Sort field")
    sort_order: Optional[str] = Field(
        "asc", pattern="^(asc|desc)$", description="Sort order"
    )
