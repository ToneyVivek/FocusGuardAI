from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import WebsiteCategory, ProductivityClassification


class BrowserActivityCreate(BaseModel):
    """
    Request schema for recording a completed browser session.
    Sent by browser extension when user switches tabs.
    
    Browser extension ONLY provides raw browser data.
    Backend determines category, productivity, and duration.
    """
    browser_name: str = Field(..., min_length=1, max_length=100, description="Browser name (e.g., Chrome, Firefox)")
    website_url: str = Field(..., max_length=2048, description="Full website URL")
    website_domain: str = Field(..., min_length=1, max_length=255, description="Website domain (e.g., github.com)")
    page_title: Optional[str] = Field(None, max_length=500, description="Page title")
    session_start_time: datetime = Field(..., description="Session start time (UTC)")
    session_end_time: datetime = Field(..., description="Session end time (UTC)")

    @field_validator("session_end_time")
    @classmethod
    def validate_session_timing(cls, v: datetime, info) -> datetime:
        """Ensure session_end_time is after session_start_time."""
        if "session_start_time" in info.data:
            start_time = info.data["session_start_time"]
            if v <= start_time:
                raise ValueError("session_end_time must be after session_start_time")
        return v

    @field_validator("website_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("website_url must start with http:// or https://")
        # Remove trailing slash for consistency
        return v.rstrip("/")

    @field_validator("website_domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Basic domain validation and normalization."""
        if "." not in v:
            raise ValueError("website_domain must be a valid domain")
        # Normalize: lowercase, strip whitespace, remove trailing dot
        return v.lower().strip().rstrip(".")


class BrowserActivityResponse(BaseModel):
    """
    Response schema for recorded browser activity.
    """
    id: int
    organization_id: int
    user_id: int
    username: Optional[str]
    browser_name: str
    website_url: str
    website_domain: str
    page_title: Optional[str]
    website_category: WebsiteCategory
    productivity_classification: ProductivityClassification
    session_start_time: datetime
    session_end_time: datetime
    duration_seconds: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
