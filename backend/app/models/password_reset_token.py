from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class PasswordResetToken(BaseModel):
    __tablename__ = "password_reset_tokens"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(String(1), default="N")  # Y/N flag for whether token has been used

    # Relationships
    user = relationship("User")

    @classmethod
    def create_token(cls, user_id: int, token: str, expires_in_hours: int = 1):
        """Create a new password reset token"""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        return cls(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            used="N"
        )

    def is_expired(self) -> bool:
        """Check if the token has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not used)"""
        return not self.is_expired() and self.used == "N"

    def mark_as_used(self):
        """Mark the token as used"""
        self.used = "Y"
