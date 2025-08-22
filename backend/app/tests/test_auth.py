import pytest

from app.core.security import (
    UserRole,
    verify_password,
    get_password_hash,
    has_permission,
)


class TestSecurity:
    """Test security functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"

        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_role_hierarchy(self):
        """Test role-based permission system"""
        # Owner should have all permissions
        assert has_permission(UserRole.OWNER, UserRole.OWNER) is True
        assert has_permission(UserRole.OWNER, UserRole.ADMIN) is True
        assert has_permission(UserRole.OWNER, UserRole.ACCOUNTANT) is True
        assert has_permission(UserRole.OWNER, UserRole.SALES_REP) is True

        # Admin should not have owner permissions
        assert has_permission(UserRole.ADMIN, UserRole.OWNER) is False
        assert has_permission(UserRole.ADMIN, UserRole.ADMIN) is True
        assert has_permission(UserRole.ADMIN, UserRole.ACCOUNTANT) is True
        assert has_permission(UserRole.ADMIN, UserRole.SALES_REP) is True

        # Sales rep should only have sales rep permissions
        assert has_permission(UserRole.SALES_REP, UserRole.OWNER) is False
        assert has_permission(UserRole.SALES_REP, UserRole.ADMIN) is False
        assert has_permission(UserRole.SALES_REP, UserRole.ACCOUNTANT) is False
        assert has_permission(UserRole.SALES_REP, UserRole.SALES_REP) is True

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        from app.core.security import (
            create_access_token,
            create_refresh_token,
            verify_token,
        )

        # Test access token
        access_token = create_access_token(
            user_id=1,
            organization_id=1,
            email="test@example.com",
            role=UserRole.OWNER.value,
        )

        payload = verify_token(access_token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["email"] == "test@example.com"
        assert payload["organization_id"] == 1
        assert payload["role"] == UserRole.OWNER.value
        assert payload["type"] == "access"

        # Test refresh token
        refresh_token = create_refresh_token(user_id=1, organization_id=1)

        refresh_payload = verify_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload["sub"] == "1"
        assert refresh_payload["organization_id"] == 1
        assert refresh_payload["type"] == "refresh"

    def test_invalid_token_verification(self):
        """Test verification of invalid tokens"""
        from app.core.security import verify_token

        # Test invalid token
        assert verify_token("invalid_token") is None
        assert verify_token("") is None

    def test_user_roles_enum(self):
        """Test UserRole enum values"""
        assert UserRole.OWNER.value == "owner"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.ACCOUNTANT.value == "accountant"
        assert UserRole.SALES_REP.value == "sales_rep"


class TestAuthenticationSchemas:
    """Test Pydantic schemas for authentication"""

    def test_login_request_validation(self):
        """Test LoginRequest schema validation"""
        from app.schemas.auth import LoginRequest

        # Valid data
        valid_data = {
            "email": "test@example.com",
            "password": "testpassword123",
        }
        login_request = LoginRequest(**valid_data)
        assert login_request.email == "test@example.com"
        assert login_request.password == "testpassword123"

        # Invalid email
        with pytest.raises(ValueError):
            LoginRequest(email="invalid-email", password="testpassword123")

        # Short password
        with pytest.raises(ValueError):
            LoginRequest(email="test@example.com", password="short")

    def test_token_response_schema(self):
        """Test Token response schema"""
        from app.schemas.auth import Token

        token_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer",
            "expires_in": 1800,
        }
        token = Token(**token_data)
        assert token.access_token == "test_access_token"
        assert token.token_type == "bearer"
        assert token.expires_in == 1800

    def test_user_response_schema(self):
        """Test UserResponse schema"""
        from app.schemas.auth import UserResponse

        user_data = {
            "id": 1,
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "owner",
            "organization_id": 1,
            "is_active": True,
            "organization_name": "Test Organization",
        }
        user_response = UserResponse(**user_data)
        assert user_response.id == 1
        assert user_response.email == "test@example.com"
        assert user_response.role == "owner"
        assert user_response.is_active is True
        assert user_response.organization_name == "Test Organization"
