from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class Payment(BaseModel):
    __tablename__ = "payments"

    invoice_id = Column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(
        String(50), nullable=False
    )  # cash, check, bank_transfer, credit_card
    reference_number = Column(String(100))
    notes = Column(String(500))

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
