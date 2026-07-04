import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_bootstrap_admin(self, client: TestClient, test_user_data):
        """Test bootstrap admin registration."""
        response = client.post(
            "/api/v1/auth/register",
            json=test_user_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == "ADMIN"
        assert "id" in data
        assert data["is_active"] is True

    def test_register_duplicate_admin(self, client: TestClient, test_user_data):
        """Test that duplicate admin registration is blocked."""
        # First registration
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Duplicate registration
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_second_admin_blocked(self, client: TestClient, test_user_data):
        """Test that second admin registration is blocked."""
        # First admin
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Second admin
        second_user = {
            "email": "admin2@example.com",
            "full_name": "Second Admin",
            "password": "SecurePassword123!",
        }
        response = client.post("/api/v1/auth/register", json=second_user)
        assert response.status_code == 403
        assert "admin registration is closed" in response.json()["detail"].lower()

    def test_login_success(self, client: TestClient, test_user_data):
        """Test successful login."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        }
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient, test_user_data):
        """Test login with invalid credentials."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "WrongPassword123!",
        }
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
        )
        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "SomePassword123!",
        }
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
        )
        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient, test_user_data):
        """Test getting current user profile."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_ready_endpoint(self, client: TestClient):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "database" in data["dependencies"]
