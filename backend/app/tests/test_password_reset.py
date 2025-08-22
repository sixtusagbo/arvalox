import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.core.security import (
    create_password_reset_token,
    verify_password_reset_token,
    get_password_hash,
    verify_password,
)
from app.models.organization import Organization
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.email_service import EmailService


class TestPasswordResetSecurity:
    """Test password reset security functions"""

    def test_password_reset_token_creation_and_verification(self):
        """Test password reset JWT token creation and verification"""
        user_id = 123

        # Create token
        token = create_password_reset_token(user_id)
        assert token is not None
        assert isinstance(token, str)

        # Verify token
        payload = verify_password_reset_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "password_reset"

        # Test invalid token
        invalid_payload = verify_password_reset_token("invalid_token")
        assert invalid_payload is None

    def test_password_reset_token_expiration(self):
        """Test password reset token expiration"""
        user_id = 123

        # Create token with short expiration
        short_expiry = timedelta(seconds=1)
        token = create_password_reset_token(user_id, short_expiry)

        # Token should be valid immediately
        payload = verify_password_reset_token(token)
        assert payload is not None

        # Wait for token to expire (in real test, you'd mock time)
        import time

        time.sleep(2)

        # Token should now be expired (JWT handles this automatically)
        expired_payload = verify_password_reset_token(token)
        assert expired_payload is None


class TestPasswordResetTokenModel:
    """Test PasswordResetToken model"""

    def test_create_token(self):
        """Test creating a password reset token"""
        user_id = 123
        token = "test_token_123"

        reset_token = PasswordResetToken.create_token(user_id, token, 2)

        assert reset_token.user_id == user_id
        assert reset_token.token == token
        assert reset_token.used == "N"
        assert reset_token.expires_at > datetime.now(timezone.utc)

    def test_token_expiration_check(self):
        """Test token expiration checking"""
        user_id = 123
        token = "test_token_123"

        # Create expired token
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used="N",
        )

        assert reset_token.is_expired() is True
        assert reset_token.is_valid() is False

    def test_token_validity_check(self):
        """Test token validity checking"""
        user_id = 123
        token = "test_token_123"

        # Create valid token
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used="N",
        )

        assert reset_token.is_expired() is False
        assert reset_token.is_valid() is True

        # Mark as used
        reset_token.mark_as_used()
        assert reset_token.used == "Y"
        assert reset_token.is_valid() is False


class TestEmailService:
    """Test email service functionality"""

    @pytest.mark.asyncio
    async def test_email_service_initialization(self):
        """Test email service initialization"""
        email_service = EmailService()

        # Check that service initializes with config values
        assert hasattr(email_service, "smtp_host")
        assert hasattr(email_service, "smtp_port")
        assert hasattr(email_service, "smtp_username")
        assert hasattr(email_service, "smtp_password")
        assert hasattr(email_service, "from_email")

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP server
        mock_server = AsyncMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service = EmailService()

        result = await email_service.send_email(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            text_content="Test Text",
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_email_failure(self, mock_smtp):
        """Test email sending failure"""
        # Mock SMTP server to raise exception
        mock_smtp.side_effect = Exception("SMTP Error")

        email_service = EmailService()

        result = await email_service.send_email(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_password_reset_email(self, mock_smtp):
        """Test sending password reset email"""
        # Mock SMTP server
        mock_server = AsyncMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service = EmailService()

        result = await email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token_123",
            user_name="John Doe",
            organization_name="Test Org",
        )

        assert result is True
        mock_server.send_message.assert_called_once()

        # Check that the email contains expected content
        call_args = mock_server.send_message.call_args[0][0]
        email_content = str(call_args)
        assert "Password Reset Request" in email_content
        assert "John Doe" in email_content
        assert "Test Org" in email_content
        assert "test_token_123" in email_content


@pytest.mark.asyncio
class TestPasswordResetEndpoints:
    """Test password reset API endpoints"""

    async def test_request_password_reset_valid_email(self, client, db_session):
        """Test password reset request with valid email"""
        # Create test organization and user
        org = Organization(
            name="Test Organization", slug="test-org", email="org@test.com"
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="user@test.com",
            first_name="John",
            last_name="Doe",
            hashed_password=get_password_hash("password123"),
            role="owner",
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Mock email service
        with patch(
            "app.services.email_service.email_service.send_password_reset_email"
        ) as mock_email:
            mock_email.return_value = True

            response = await client.post(
                "/api/v1/auth/password-reset/request",
                json={"email": "user@test.com"},
            )

        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]
        mock_email.assert_called_once()

    async def test_request_password_reset_invalid_email(
        self, client, db_session
    ):
        """Test password reset request with invalid email"""
        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "nonexistent@test.com"},
        )

        assert response.status_code == 200
        # Should return same message for security (don't reveal if email exists)
        assert "password reset link has been sent" in response.json()["message"]

    async def test_request_password_reset_inactive_user(
        self, client, db_session
    ):
        """Test password reset request for inactive user"""
        # Create test organization and inactive user
        org = Organization(
            name="Test Organization", slug="test-org", email="org@test.com"
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="inactive@test.com",
            first_name="Jane",
            last_name="Doe",
            hashed_password=get_password_hash("password123"),
            role="owner",
            organization_id=org.id,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "inactive@test.com"},
        )

        assert response.status_code == 200
        # Should return same message for security
        assert "password reset link has been sent" in response.json()["message"]

    async def test_confirm_password_reset_valid_token(self, client, db_session):
        """Test password reset confirmation with valid token"""
        # Create test organization and user
        org = Organization(
            name="Test Organization", slug="test-org", email="org@test.com"
        )
        db_session.add(org)
        await db_session.flush()

        original_password = "oldpassword123"
        user = User(
            email="user@test.com",
            first_name="John",
            last_name="Doe",
            hashed_password=get_password_hash(original_password),
            role="owner",
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        # Create valid reset token
        reset_token = create_password_reset_token(user.id)
        db_token = PasswordResetToken.create_token(
            user_id=user.id, token=reset_token, expires_in_hours=1
        )
        db_session.add(db_token)
        await db_session.commit()

        new_password = "newpassword123"
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": new_password},
        )

        assert response.status_code == 200
        assert (
            "Password has been reset successfully" in response.json()["message"]
        )

        # Verify password was changed
        await db_session.refresh(user)
        assert verify_password(new_password, user.hashed_password) is True
        assert verify_password(original_password, user.hashed_password) is False

        # Verify token was marked as used
        await db_session.refresh(db_token)
        assert db_token.used == "Y"

    async def test_confirm_password_reset_invalid_token(
        self, client, db_session
    ):
        """Test password reset confirmation with invalid token"""
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "invalid_token", "new_password": "newpassword123"},
        )

        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    async def test_confirm_password_reset_expired_token(
        self, client, db_session
    ):
        """Test password reset confirmation with expired token"""
        # Create test organization and user
        org = Organization(
            name="Test Organization", slug="test-org", email="org@test.com"
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="user@test.com",
            first_name="John",
            last_name="Doe",
            hashed_password=get_password_hash("password123"),
            role="owner",
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        # Create expired reset token
        reset_token = create_password_reset_token(
            user.id, timedelta(seconds=-1)
        )
        db_token = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used="N",
        )
        db_session.add(db_token)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": "newpassword123"},
        )

        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    async def test_confirm_password_reset_used_token(self, client, db_session):
        """Test password reset confirmation with already used token"""
        # Create test organization and user
        org = Organization(
            name="Test Organization", slug="test-org", email="org@test.com"
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="user@test.com",
            first_name="John",
            last_name="Doe",
            hashed_password=get_password_hash("password123"),
            role="owner",
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        # Create used reset token
        reset_token = create_password_reset_token(user.id)
        db_token = PasswordResetToken.create_token(
            user_id=user.id, token=reset_token, expires_in_hours=1
        )
        db_token.mark_as_used()  # Mark as used
        db_session.add(db_token)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": "newpassword123"},
        )

        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    async def test_confirm_password_reset_nonexistent_user(
        self, client, db_session
    ):
        """Test password reset confirmation for nonexistent user"""
        # Create token for nonexistent user
        reset_token = create_password_reset_token(99999)  # Non-existent user ID

        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": "newpassword123"},
        )

        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]
