from datetime import datetime, timedelta, timezone
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    SALES_REP = "sales_rep"


def create_access_token(
    user_id: int,
    organization_id: int,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token with organization context and role"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "organization_id": organization_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: int, organization_id: int) -> str:
    """Create JWT refresh token"""
    expire = datetime.now(timezone.utc) + timedelta(days=30)

    to_encode = {
        "sub": str(user_id),
        "organization_id": organization_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_token(token: str) -> dict | None:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def has_permission(user_role: str, required_role: str) -> bool:
    """Check if user role has permission for required role"""
    role_hierarchy = {
        UserRole.OWNER: 4,
        UserRole.ADMIN: 3,
        UserRole.ACCOUNTANT: 2,
        UserRole.SALES_REP: 1,
    }

    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    return user_level >= required_level
