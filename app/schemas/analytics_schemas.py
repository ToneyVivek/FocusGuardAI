from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import WebsiteCategory, ProductivityClassification
from app.services.domain_normalization import domain_normalization_service


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
        """
        Ensure session_end_time is after session_start_time and within 24 hours.
        
        Validates:
        1. session_end_time must be after session_start_time
        2. Session duration cannot exceed 24 hours (86400 seconds)
        """
        if "session_start_time" in info.data:
            start_time = info.data["session_start_time"]
            if v <= start_time:
                raise ValueError("session_end_time must be after session_start_time")
            
            # Check maximum duration (24 hours)
            duration_seconds = (v - start_time).total_seconds()
            if duration_seconds > 86400:
                raise ValueError("session duration cannot exceed 24 hours")
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
        """
        Validate and normalize domain using centralized service.
        
        Uses DomainNormalizationService for consistent normalization across
        all analytics operations.
        """
        return domain_normalization_service.normalize_domain(v)


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


class UserSummary(BaseModel):
    id: int
    username: str
    email: str


class WebsiteDetail(BaseModel):
    """Aggregated activity for a single website, ordered by total time spent."""

    name: str = Field(..., description="Friendly display name for the website")
    domain: str = Field(..., description="Normalized website domain")
    url: str = Field(..., description="Representative URL for this website")
    time_spent: str = Field(..., description="Total time spent in HH:MM:SS format")
    duration_seconds: int = Field(..., ge=0, description="Total time spent in seconds")
    visits: int = Field(..., ge=0, description="Number of tab sessions recorded")
    percentage: float = Field(
        ...,
        ge=0,
        description="Share of total tracked time (website duration / total time × 100)",
    )


class CategoryDetail(BaseModel):
    """Aggregated activity for a website category, ordered by total time spent."""

    category: str = Field(..., description="Website category display name")
    time_spent: str = Field(..., description="Total time spent in HH:MM:SS format")
    duration_seconds: int = Field(..., ge=0, description="Total time spent in seconds")
    percentage: float = Field(
        ...,
        ge=0,
        description="Share of total tracked time (category duration / total time × 100)",
    )


class AnalyticsSummaryResponse(BaseModel):
    user: UserSummary
    productive_time: str
    non_productive_time: str
    neutral_time: str
    total_websites_visited: int
    total_tab_switches: int
    total_time: str
    last_activity_at: Optional[datetime] = Field(
        None,
        description="Latest session_end_time for the authenticated user (UTC)",
    )
    category_summary: list[CategoryDetail] = Field(
        ...,
        description="Categories ordered by total time spent (highest first)",
    )
    website_summary: list[WebsiteDetail] = Field(
        ...,
        description="Websites ordered by total time spent (highest first)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": 1,
                    "username": "Jane Doe",
                    "email": "jane@example.com",
                },
                "productive_time": "01:38:22",
                "non_productive_time": "00:20:15",
                "neutral_time": "00:00:00",
                "total_websites_visited": 12,
                "total_tab_switches": 87,
                "total_time": "01:58:37",
                "last_activity_at": "2026-07-11T18:13:58Z",
                "category_summary": [
                    {
                        "category": "Development",
                        "time_spent": "01:20:40",
                        "duration_seconds": 4840,
                        "percentage": 67.89,
                    },
                    {
                        "category": "AI Tool",
                        "time_spent": "00:18:42",
                        "duration_seconds": 1122,
                        "percentage": 15.75,
                    },
                ],
                "website_summary": [
                    {
                        "name": "GitHub",
                        "domain": "github.com",
                        "url": "https://github.com",
                        "time_spent": "01:20:40",
                        "duration_seconds": 4840,
                        "visits": 25,
                        "percentage": 67.89,
                    },
                    {
                        "name": "ChatGPT",
                        "domain": "chat.openai.com",
                        "url": "https://chat.openai.com",
                        "time_spent": "00:18:42",
                        "duration_seconds": 1122,
                        "visits": 10,
                        "percentage": 15.75,
                    },
                ],
            }
        }
    )

