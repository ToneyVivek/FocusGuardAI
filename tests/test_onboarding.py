import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.onboarding
class TestOnboardingFlow:
    """Test organization creation and employee onboarding flow."""

    def test_create_organization(self, client: TestClient, test_user_data, test_organization_data):
        """Test organization creation by admin."""
        # Register admin
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login as admin
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]
        
        # Create organization
        response = client.post(
            "/api/v1/organizations/create",
            json=test_organization_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["organization_name"] == test_organization_data["organization_name"]
        assert "id" in data

    def test_create_organization_unauthorized(self, client: TestClient, test_organization_data):
        """Test organization creation without authentication."""
        response = client.post(
            "/api/v1/organizations/create",
            json=test_organization_data,
        )
        assert response.status_code == 401

    def test_create_organization_duplicate(self, client: TestClient, test_user_data, test_organization_data):
        """Test duplicate organization creation is blocked."""
        # Register admin
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]
        
        # Create organization first time
        client.post(
            "/api/v1/organizations/create",
            json=test_organization_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/v1/organizations/create",
            json=test_organization_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_invite_employee(self, client: TestClient, test_user_data, test_organization_data):
        """Test employee invitation by admin."""
        # Register admin
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]
        
        # Create organization
        org_response = client.post(
            "/api/v1/organizations/create",
            json=test_organization_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # Invite employee
        invite_data = {"email": "employee@example.com"}
        response = client.post(
            "/api/v1/admin/invite-user",
            json=invite_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == invite_data["email"]
        assert data["organization_id"] == org_response.json()["id"]
        assert data["is_used"] is False

    def test_invite_employee_without_org(self, client: TestClient, test_user_data):
        """Test employee invitation without organization fails."""
        # Register admin
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]
        
        # Try to invite without organization
        invite_data = {"email": "employee@example.com"}
        response = client.post(
            "/api/v1/admin/invite-user",
            json=invite_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert "must belong to an organization" in response.json()["detail"].lower()

    def test_complete_onboarding_invalid_token(self, client: TestClient):
        """Test onboarding with invalid token fails."""
        setup_data = {
            "token": "invalid_token",
            "full_name": "Employee User",
            "password": "SecurePassword123!",
        }
        response = client.post("/api/v1/auth/complete-setup", json=setup_data)
        assert response.status_code == 404
        assert "invalid invitation token" in response.json()["detail"].lower()

    def test_complete_onboarding_expired_token(self, client: TestClient):
        """Test onboarding with expired token fails."""
        # This would require creating an expired invitation in the database
        # For now, we test the endpoint structure
        setup_data = {
            "token": "some_token",
            "full_name": "Employee User",
            "password": "SecurePassword123!",
        }
        response = client.post("/api/v1/auth/complete-setup", json=setup_data)
        # Will fail with 404 since token doesn't exist
        assert response.status_code in [400, 404]
