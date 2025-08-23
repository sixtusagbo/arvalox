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

    def test_register_request_validation(self):
        """Test RegisterRequest schema validation"""
        from app.schemas.auth import RegisterRequest

        # Valid data with currency
        valid_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "organization_name": "Test Organization",
            "organization_slug": "test-org",
            "currency_code": "NGN",
            "currency_symbol": "₦",
            "currency_name": "Nigerian Naira",
        }
        register_request = RegisterRequest(**valid_data)
        assert register_request.email == "test@example.com"
        assert register_request.organization_name == "Test Organization"
        assert register_request.currency_code == "NGN"
        assert register_request.currency_symbol == "₦"
        assert register_request.currency_name == "Nigerian Naira"

        # Valid data without currency (should allow None)
        minimal_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "organization_name": "Test Organization",
        }
        minimal_request = RegisterRequest(**minimal_data)
        assert minimal_request.currency_code is None
        assert minimal_request.currency_symbol is None
        assert minimal_request.currency_name is None

        # Invalid currency code (too long)
        with pytest.raises(ValueError):
            RegisterRequest(**{
                **valid_data,
                "currency_code": "NGNN"  # 4 chars, should be 3
            })

        # Invalid currency code (too short)
        with pytest.raises(ValueError):
            RegisterRequest(**{
                **valid_data,
                "currency_code": "NG"  # 2 chars, should be 3
            })

    def test_organization_update_schema(self):
        """Test OrganizationUpdate schema validation"""
        from app.schemas.auth import OrganizationUpdate

        # Valid currency update
        update_data = {
            "currency_code": "USD",
            "currency_symbol": "$",
            "currency_name": "US Dollar",
        }
        org_update = OrganizationUpdate(**update_data)
        assert org_update.currency_code == "USD"
        assert org_update.currency_symbol == "$"
        assert org_update.currency_name == "US Dollar"

        # Partial update (only name)
        partial_update = OrganizationUpdate(name="New Organization Name")
        assert partial_update.name == "New Organization Name"
        assert partial_update.currency_code is None
