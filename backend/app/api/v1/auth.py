from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    UserRole,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_password_reset_token,
    verify_token,
)
from app.models.organization import Organization
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.email_service import email_service
from app.schemas.auth import (
    LoginRequest,
    OrganizationUpdate,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    Token,
    UserProfileUpdate,
    UserResponse,
)

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user and organization"""

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization
    organization = Organization(
        name=user_data.organization_name,
        slug=user_data.organization_slug
        or user_data.organization_name.lower().replace(" ", "-"),
        email=user_data.email,
    )
    db.add(organization)
    await db.flush()  # Get the organization ID

    # Create user as organization owner
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        role=UserRole.OWNER.value,
        organization_id=organization.id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create tokens
    access_token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        role=user.role,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        organization_id=user.organization_id,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
    )


@router.post("/login", response_model=Token)
async def login(
    user_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate user and return tokens"""

    # Get user by email
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(
        user_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )

    # Create tokens
    access_token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        role=user.role,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        organization_id=user.organization_id,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Refresh access token using refresh token"""

    payload = verify_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user from database
    user = await db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        role=user.role,
    )
    new_refresh_token = create_refresh_token(
        user_id=user.id,
        organization_id=user.organization_id,
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current user information"""
    # Load user with organization
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()

    # Get organization info
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    organization = org_result.scalar_one()

    # Convert to response format
    user_dict = {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "organization_id": user.organization_id,
        "is_active": user.is_active,
        "organization_name": organization.name,
    }

    return user_dict


@router.post("/logout")
async def logout() -> Any:
    """Logout user (client should discard tokens)"""
    return {"message": "Successfully logged out"}


@router.post("/password-reset/request")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Request password reset by email"""

    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request_data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal if email exists or not for security
        return {
            "message": "If the email exists, a password reset link has been sent"
        }

    if not user.is_active:
        return {
            "message": "If the email exists, a password reset link has been sent"
        }

    # Generate reset token
    reset_token = create_password_reset_token(user.id)

    # Store token in database
    password_reset_token = PasswordResetToken.create_token(
        user_id=user.id, token=reset_token, expires_in_hours=1
    )
    db.add(password_reset_token)
    await db.commit()

    # Get organization for email
    organization = await db.get(Organization, user.organization_id)

    # Send email
    user_name = f"{user.first_name} {user.last_name}"
    await email_service.send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        user_name=user_name,
        organization_name=organization.name if organization else "Arvalox",
    )

    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Confirm password reset with token and new password"""

    # Verify JWT token
    payload = verify_password_reset_token(confirm_data.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    # Check if token exists in database and is valid
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == confirm_data.token,
            PasswordResetToken.user_id == int(user_id),
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token or not db_token.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    user = await db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or inactive",
        )

    # Update password
    user.hashed_password = get_password_hash(confirm_data.new_password)

    # Mark token as used
    db_token.mark_as_used()

    await db.commit()

    return {"message": "Password has been reset successfully"}


@router.put("/me/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update user profile information"""
    
    # Check if email is being changed and already exists
    if profile_data.email and profile_data.email != current_user.email:
        result = await db.execute(
            select(User).where(
                User.email == profile_data.email,
                User.id != current_user.id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update user fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    # Get organization info for response
    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = org_result.scalar_one()
    
    # Return updated user info
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "organization_id": current_user.organization_id,
        "is_active": current_user.is_active,
        "organization_name": organization.name,
    }
    
    return user_dict


@router.put("/me/password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Change user password"""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    
    await db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/me/organization", response_model=dict)
async def get_organization_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get organization information"""
    
    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = org_result.scalar_one()
    
    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "created_at": organization.created_at,
        "updated_at": organization.updated_at,
    }


@router.put("/me/organization")
async def update_organization(
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update organization information (owner/admin only)"""
    
    # Check if user has permission to update organization
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and admins can update organization details"
        )
    
    # Get organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = org_result.scalar_one()
    
    # Check if slug is being changed and already exists
    if org_data.slug and org_data.slug != organization.slug:
        slug_result = await db.execute(
            select(Organization).where(
                Organization.slug == org_data.slug,
                Organization.id != organization.id
            )
        )
        if slug_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already exists"
            )
    
    # Update organization fields
    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    await db.commit()
    await db.refresh(organization)
    
    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "created_at": organization.created_at,
        "updated_at": organization.updated_at,
    }
