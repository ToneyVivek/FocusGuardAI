from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import UserRole


# ----------------- User Schemas -----------------
class AdminRegisterRequest(BaseModel):
    """Public bootstrap registration — first admin only. No role or organization_id accepted."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    organization_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------- Token Schemas -----------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithRefresh(BaseModel):
    """Response schema including both access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "xK9mP2vQ8jR4nT6wY1zA5bC7dE3fG9hI2jK4lM6nO8pQ0rS2tU4vW6xY8zA0bC2",
                "token_type": "bearer",
            }
        }
    )


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "xK9mP2vQ8jR4nT6wY1zA5bC7dE3fG9hI2jK4lM6nO8pQ0rS2tU4vW6xY8zA0bC2",
            }
        }
    )


class LogoutRequest(BaseModel):
    """Request schema for logout."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "xK9mP2vQ8jR4nT6wY1zA5bC7dE3fG9hI2jK4lM6nO8pQ0rS2tU4vW6xY8zA0bC2",
            }
        }
    )


# ----------------- Organization Schemas -----------------
class OrganizationCreate(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=100)


class OrganizationResponse(BaseModel):
    id: int
    organization_name: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


# ----------------- Invitation Schemas -----------------
class InvitationCreate(BaseModel):
    email: EmailStr


class InvitationResponse(BaseModel):
    """Public invitation response — token is never exposed (delivered via email only)."""

    id: int
    email: EmailStr
    organization_id: int
    invited_by: int
    expires_at: datetime
    is_used: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OnboardingSetup(BaseModel):
    token: str
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
