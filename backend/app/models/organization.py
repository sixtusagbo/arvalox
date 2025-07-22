from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    address = Column(String(500))

    # Subscription info
    subscription_plan = Column(
        String(50), default="trial"
    )  # trial, starter, professional, enterprise
    subscription_status = Column(
        String(50), default="active"
    )  # active, cancelled, past_due, unpaid
    trial_ends_at = Column(DateTime(timezone=True))

    # Usage limits
    invoice_limit = Column(Integer, default=10)
    user_limit = Column(Integer, default=1)

    # Relationships
    users = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    customers = relationship(
        "Customer", back_populates="organization", cascade="all, delete-orphan"
    )
    invoices = relationship(
        "Invoice", back_populates="organization", cascade="all, delete-orphan"
    )
