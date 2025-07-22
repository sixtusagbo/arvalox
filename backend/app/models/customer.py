from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_code = Column(String(50), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    billing_address = Column(String(500))
    shipping_address = Column(String(500))
    credit_limit = Column(Numeric(15, 2), default=0.00)
    payment_terms = Column(Integer, default=30)  # days
    tax_id = Column(String(50))
    status = Column(String(20), default="active")  # active, inactive, suspended

    # Relationships
    organization = relationship("Organization", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer")

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "customer_code", name="uq_org_customer_code"
        ),
    )
