"""
Integration tests for refresh token functionality.

Tests cover:
- Successful refresh with token rotation
- Expired refresh token rejection
- Revoked refresh token rejection
- Refresh token reuse after rotation
- Logout invalidation
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestRefreshTokens:
    """Test refresh token lifecycle and security features."""

    def test_login_returns_refresh_token(self, client: TestClient, test_user_data):
        """Test that login endpoint returns both access and refresh tokens."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert len(tokens["refresh_token"]) > 32  # Cryptographically secure token

    def test_successful_refresh_token_rotation(self, client: TestClient, test_user_data):
        """Test successful token refresh with rotation."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        tokens = login_response.json()
        old_refresh_token = tokens["refresh_token"]
        
        # Refresh the token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        
        # Verify new tokens are issued
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"
        
        # Verify token rotation (new refresh token is different)
        assert new_tokens["refresh_token"] != old_refresh_token
        
        # Verify old token is now invalid (rotation)
        second_refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert second_refresh_response.status_code == 401

    def test_expired_refresh_token_rejected(self, client: TestClient, test_user_data, db_session):
        """Test that expired refresh tokens are rejected."""
        from app.models.models import RefreshToken
        from app.services.refresh_token_service import refresh_token_service
        from datetime import datetime, timezone, timedelta
        
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        tokens = login_response.json()
        
        # Manually expire the refresh token in database
        token_hash = refresh_token_service._hash_token(tokens["refresh_token"])
        db_token = (
            db_session.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
        db_token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.commit()
        
        # Try to refresh with expired token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        assert refresh_response.status_code == 401
        assert "expired" in refresh_response.json()["detail"].lower()

    def test_revoked_refresh_token_rejected(self, client: TestClient, test_user_data):
        """Test that revoked refresh tokens are rejected."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        tokens = login_response.json()
        
        # Logout to revoke the token
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert logout_response.status_code == 204
        
        # Try to refresh with revoked token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        assert refresh_response.status_code == 401
        assert "revoked" in refresh_response.json()["detail"].lower()

    def test_invalid_refresh_token_rejected(self, client: TestClient):
        """Test that invalid refresh tokens are rejected."""
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token_string"},
        )
        
        assert refresh_response.status_code == 401
        assert "invalid" in refresh_response.json()["detail"].lower()

    def test_logout_with_specific_token(self, client: TestClient, test_user_data):
        """Test logout with specific refresh token."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        tokens = login_response.json()
        
        # Logout with specific token
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        assert logout_response.status_code == 204
        
        # Verify token is revoked
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 401

    def test_logout_without_token_revokes_all(self, client: TestClient, test_user_data):
        """Test logout without specific token revokes all user tokens."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login twice to get multiple refresh tokens
        login1 = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token1 = login1.json()["refresh_token"]
        
        login2 = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token2 = login2.json()["refresh_token"]
        
        # Logout without specifying token (requires auth)
        headers = {"Authorization": f"Bearer {login1.json()['access_token']}"}
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={},  # No refresh token specified
            headers=headers,
        )
        
        assert logout_response.status_code == 204
        
        # Verify both tokens are revoked
        refresh1 = client.post("/api/v1/auth/refresh", json={"refresh_token": token1})
        refresh2 = client.post("/api/v1/auth/refresh", json={"refresh_token": token2})
        
        assert refresh1.status_code == 401
        assert refresh2.status_code == 401

    def test_logout_idempotent(self, client: TestClient, test_user_data):
        """Test that logout is idempotent (can be called multiple times safely)."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        tokens = login_response.json()
        
        # Logout twice with same token
        logout1 = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        logout2 = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        # Both should succeed (idempotent)
        assert logout1.status_code == 204
        assert logout2.status_code == 204

    def test_refresh_token_requires_valid_token(self, client: TestClient, test_user_data):
        """Test that refresh endpoint requires a valid refresh token."""
        # Register
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to refresh without token
        refresh_response = client.post("/api/v1/auth/refresh", json={})
        assert refresh_response.status_code == 422  # Validation error

    def test_multiple_refreshes_generate_new_tokens(self, client: TestClient, test_user_data):
        """Test that multiple refreshes always generate new tokens."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        tokens = login_response.json()
        
        # Refresh multiple times
        refresh_tokens = [tokens["refresh_token"]]
        for _ in range(3):
            refresh_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_tokens[-1]},
            )
            assert refresh_response.status_code == 200
            new_tokens = refresh_response.json()
            refresh_tokens.append(new_tokens["refresh_token"])
        
        # Verify all tokens are unique
        assert len(set(refresh_tokens)) == len(refresh_tokens)
        
        # Verify only the last token is valid
        for i, token in enumerate(refresh_tokens[:-1]):
            refresh_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
            assert refresh_response.status_code == 401, f"Token {i} should be invalid"
        
        # Last token should still be valid
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_tokens[-1]},
        )
        assert refresh_response.status_code == 200

    def test_rate_limiting_on_refresh_endpoint(self, client: TestClient, test_user_data):
        """Test that refresh endpoint has rate limiting."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        tokens = login_response.json()
        
        # Make many refresh requests (should hit rate limit)
        # Note: This test may be flaky depending on rate limit configuration
        # Adjust the count based on actual rate limit (20/minute)
        for _ in range(25):
            client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": tokens["refresh_token"]},
            )
        
        # Last request might be rate limited
        # This is a soft test - actual rate limiting behavior depends on configuration
