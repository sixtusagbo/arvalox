from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token, has_permission, UserRole
from app.models.user import User
from app.schemas.auth import TokenData

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    # Verify token type
    if payload.get("type") != "access":
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    user = await db.get(User, int(user_id))
    if user is None:
        raise credentials_exception

    # Verify organization context matches
    if user.organization_id != payload.get("organization_id"):
        raise credentials_exception

    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (alias for clarity)"""
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, required_role.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


# Convenience dependencies for common roles
require_owner = require_role(UserRole.OWNER)
require_admin = require_role(UserRole.ADMIN)
require_accountant = require_role(UserRole.ACCOUNTANT)
require_sales_rep = require_role(UserRole.SALES_REP)


async def get_organization_context(
    current_user: User = Depends(get_current_user),
) -> int:
    """Get organization ID from current user context"""
    return current_user.organization_id
