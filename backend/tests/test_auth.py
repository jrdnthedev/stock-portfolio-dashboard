"""Tests for JWT authentication middleware and utilities."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.middleware.auth import (
    AuthenticationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
    get_current_user,
    hash_password,
    require_any_role,
    require_role,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test that password hashing produces a bcrypt hash."""
        password = "my_secure_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "my_secure_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification with wrong password."""
        password = "my_secure_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_produces_different_results(self):
        """Test that hashing the same password twice produces different hashes."""
        password = "my_secure_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "user@example.com", "role": "admin"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test creating access token with custom expiration."""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=5)

        token = create_access_token(data, expires_delta=expires_delta)
        payload = decode_token(token)

        # Check expiration is approximately 5 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(UTC) + expires_delta

        # Allow 5 second tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        data = {"sub": "user@example.com"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_longer_expiry(self):
        """Test that refresh tokens have longer expiration than access tokens."""
        data = {"sub": "user@example.com"}

        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        # Refresh token should expire later
        assert refresh_payload["exp"] > access_payload["exp"]


class TestTokenDecoding:
    """Test JWT token decoding and validation."""

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "user@example.com", "role": "user"}
        token = create_access_token(data)

        payload = decode_token(token)

        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "user"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token raises error."""
        invalid_token = "invalid.token.here"

        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(invalid_token)

        assert "Invalid or expired token" in str(exc_info.value)

    def test_decode_expired_token(self):
        """Test decoding an expired token raises error."""
        data = {"sub": "user@example.com"}
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        token = create_access_token(data, expires_delta=expires_delta)

        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(token)

        assert "Invalid or expired token" in str(exc_info.value)


class TestAuthDependencies:
    """Test FastAPI authentication dependencies."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with auth dependencies."""
        from fastapi import Depends

        app = FastAPI()

        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"message": f"Hello {user['sub']}"}

        @app.get("/active")
        async def active_route(user: dict = Depends(get_current_active_user)):
            return {"message": f"Active user {user['sub']}"}

        @app.get("/admin")
        async def admin_route(user: dict = Depends(require_role("admin"))):
            _ = user
            return {"message": "Admin access granted"}

        @app.get("/moderator")
        async def mod_route(user: dict = Depends(require_any_role(["admin", "moderator"]))):
            _ = user
            return {"message": "Moderator access granted"}

        return app

    def test_protected_route_with_valid_token(self, app):
        """Test accessing protected route with valid token."""
        client = TestClient(app)

        # Create token
        token = create_access_token({"sub": "user@example.com"})

        # Make request with token
        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json()["message"] == "Hello user@example.com"

    def test_protected_route_without_token(self, app):
        """Test accessing protected route without token fails."""
        client = TestClient(app)

        response = client.get("/protected")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_protected_route_with_invalid_token(self, app):
        """Test accessing protected route with invalid token fails."""
        client = TestClient(app)

        response = client.get("/protected", headers={"Authorization": "Bearer invalid.token.here"})

        assert response.status_code == 401

    def test_active_user_with_active_account(self, app):
        """Test active user dependency with active account."""
        client = TestClient(app)

        token = create_access_token({"sub": "user@example.com", "disabled": False})

        response = client.get("/active", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

    def test_active_user_with_disabled_account(self, app):
        """Test active user dependency rejects disabled account."""
        client = TestClient(app)

        token = create_access_token({"sub": "user@example.com", "disabled": True})

        response = client.get("/active", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]

    def test_role_requirement_with_correct_role(self, app):
        """Test role requirement with correct role."""
        client = TestClient(app)

        token = create_access_token({"sub": "admin@example.com", "role": "admin"})

        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert "Admin access granted" in response.json()["message"]

    def test_role_requirement_with_wrong_role(self, app):
        """Test role requirement with wrong role fails."""
        client = TestClient(app)

        token = create_access_token({"sub": "user@example.com", "role": "user"})

        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_any_role_requirement_with_matching_role(self, app):
        """Test multiple role requirement with matching role."""
        client = TestClient(app)

        # Test with admin role
        token = create_access_token({"sub": "admin@example.com", "role": "admin"})
        response = client.get("/moderator", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        # Test with moderator role
        token = create_access_token({"sub": "mod@example.com", "role": "moderator"})
        response = client.get("/moderator", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_any_role_requirement_with_non_matching_role(self, app):
        """Test multiple role requirement with non-matching role fails."""
        client = TestClient(app)

        token = create_access_token({"sub": "user@example.com", "role": "user"})

        response = client.get("/moderator", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403

    def test_refresh_token_rejected_for_authentication(self, app):
        """Test that refresh tokens cannot be used for regular authentication."""
        client = TestClient(app)

        # Create refresh token
        token = create_refresh_token({"sub": "user@example.com"})

        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401
        assert "refresh token cannot be used" in response.json()["detail"]


class TestTokenPayload:
    """Test token payload validation."""

    def test_token_without_subject_fails(self):
        """Test that token without 'sub' claim fails validation."""
        app = FastAPI()

        @app.get("/test")
        async def test_route(user: dict = Depends(get_current_user)):
            return user

        client = TestClient(app)

        # Create token without 'sub'
        token = create_access_token({"role": "admin"})

        response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401
        assert "missing subject" in response.json()["detail"]
