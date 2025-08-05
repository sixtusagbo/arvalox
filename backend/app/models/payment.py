from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import BaseModel


class Payment(BaseModel):
    __tablename__ = "payments"

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_id = Column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # User who recorded the payment
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(
        String(50), nullable=False
    )  # cash, check, bank_transfer, credit_card, online
    reference_number = Column(String(100))
    notes = Column(String(500))
    status = Column(
        String(20), nullable=False, default="completed"
    )  # completed, pending, failed, cancelled

    # Relationships
    organization = relationship("Organization")
    invoice = relationship("Invoice", back_populates="payments")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "reference_number",
            name="uq_org_payment_reference",
        ),
    )
