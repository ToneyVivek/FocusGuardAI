from datetime import datetime
from typing import Optional, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import UserRole

DataType = TypeVar("DataType")


class APIResponse(BaseModel, Generic[DataType]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[DataType] = None


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


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


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
