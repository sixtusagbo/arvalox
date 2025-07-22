from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # owner, admin, accountant, sales_rep
    is_active = Column(Boolean, default=True)
    invited_at = Column(DateTime(timezone=True))
    joined_at = Column(DateTime(timezone=True))

    # Relationships
    organization = relationship("Organization", back_populates="users")
    invoices = relationship("Invoice", back_populates="user")

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_org_user_email"),
    )
