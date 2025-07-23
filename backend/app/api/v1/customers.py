from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerSearchParams,
    CustomerUpdate,
)

router = APIRouter()


@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new customer"""

    # Check if customer_code already exists for this organization
    existing_customer = await db.execute(
        select(Customer).where(
            and_(
                Customer.organization_id == current_user.organization_id,
                Customer.customer_code == customer_data.customer_code,
            )
        )
    )
    if existing_customer.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Customer code already exists in your organization",
        )

    # Create new customer
    customer = Customer(
        organization_id=current_user.organization_id,
        **customer_data.model_dump(),
    )

    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return customer


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    search: Optional[str] = Query(
        None, description="Search in customer_code, contact_name, email, phone"
    ),
    status: Optional[str] = Query(
        None,
        pattern="^(active|inactive|suspended)$",
        description="Filter by status",
    ),
    payment_terms_min: Optional[int] = Query(
        None, ge=0, description="Minimum payment terms"
    ),
    payment_terms_max: Optional[int] = Query(
        None, ge=0, description="Maximum payment terms"
    ),
    has_credit_limit: Optional[bool] = Query(
        None, description="Filter customers with credit limit"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("contact_name", description="Sort field"),
    sort_order: Optional[str] = Query(
        "asc", pattern="^(asc|desc)$", description="Sort order"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List customers with search and filtering"""

    # Base query with organization filtering
    query = select(Customer).where(
        Customer.organization_id == current_user.organization_id
    )

    # Apply search filter
    if search:
        search_filter = or_(
            Customer.customer_code.ilike(f"%{search}%"),
            Customer.contact_name.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%"),
            Customer.phone.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    # Apply status filter
    if status:
        query = query.where(Customer.status == status)

    # Apply payment terms filters
    if payment_terms_min is not None:
        query = query.where(Customer.payment_terms >= payment_terms_min)
    if payment_terms_max is not None:
        query = query.where(Customer.payment_terms <= payment_terms_max)

    # Apply credit limit filter
    if has_credit_limit is not None:
        if has_credit_limit:
            query = query.where(Customer.credit_limit > 0)
        else:
            query = query.where(Customer.credit_limit == 0)

    # Apply sorting
    sort_column = getattr(Customer, sort_by, Customer.contact_name)
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
    customers = result.scalars().all()

    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page

    return CustomerListResponse(
        customers=customers,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific customer by ID"""

    customer = await db.execute(
        select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == current_user.organization_id,
            )
        )
    )
    customer = customer.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a customer"""

    # Get existing customer
    customer = await db.execute(
        select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == current_user.organization_id,
            )
        )
    )
    customer = customer.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Check if customer_code is being updated and already exists
    if (
        customer_data.customer_code
        and customer_data.customer_code != customer.customer_code
    ):
        existing_customer = await db.execute(
            select(Customer).where(
                and_(
                    Customer.organization_id == current_user.organization_id,
                    Customer.customer_code == customer_data.customer_code,
                    Customer.id != customer_id,
                )
            )
        )
        if existing_customer.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Customer code already exists in your organization",
            )

    # Update customer fields
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)

    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a customer"""

    customer = await db.execute(
        select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == current_user.organization_id,
            )
        )
    )
    customer = customer.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await db.delete(customer)
    await db.commit()

    return {"message": "Customer deleted successfully"}
