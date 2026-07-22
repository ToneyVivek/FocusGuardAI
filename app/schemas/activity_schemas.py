from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config.config import settings


class ActivityEventCreate(BaseModel):
    """
    Request schema for recording a single activity event.
    Sent by browser extension when user performs browser actions.
    
    Browser extension provides raw event data.
    Backend determines organization_id and user_id from JWT.
    """
    event_id: str = Field(..., min_length=1, max_length=100, description="Unique event ID from extension (UUID)")
    event_type: str = Field(..., min_length=1, max_length=50, description="Event type (e.g., TAB_CREATED, TAB_ACTIVATED)")
    browser_name: str = Field(..., min_length=1, max_length=100, description="Browser name (e.g., Chrome, Firefox)")
    tab_id: Optional[int] = Field(None, description="Tab ID (nullable for lifecycle events)")
    window_id: Optional[int] = Field(None, description="Window ID (nullable for lifecycle events)")
    website_url: Optional[str] = Field(None, max_length=2048, description="Website URL (nullable for non-tab events)")
    website_domain: Optional[str] = Field(None, max_length=255, description="Website domain (nullable for non-tab events)")
    page_title: Optional[str] = Field(None, max_length=500, description="Page title")
    previous_url: Optional[str] = Field(None, max_length=2048, description="Previous URL for navigation events")
    previous_domain: Optional[str] = Field(None, max_length=255, description="Previous domain for navigation events")
    timestamp: datetime = Field(..., description="Event timestamp (UTC)")
    event_metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata", description="Additional event metadata (JSON)")

    @field_validator("website_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Basic URL validation if provided."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("website_url must start with http:// or https://")
        # Remove trailing slash for consistency
        return v.rstrip("/") if v else v

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event type is one of the allowed types."""
        allowed_types = {
            "TAB_CREATED",
            "TAB_UPDATED",
            "TAB_ACTIVATED",
            "TAB_CLOSED",
            "WINDOW_FOCUS_GAINED",
            "WINDOW_FOCUS_LOST",
            "BROWSER_STARTUP",
            "BROWSER_SHUTDOWN",
            "IDLE_STARTED",
            "IDLE_ENDED",
            "SESSION_STARTED",
            "SESSION_ENDED",
        }
        if v not in allowed_types:
            raise ValueError(f"event_type must be one of: {', '.join(sorted(allowed_types))}")
        return v


class ActivityEventBatchCreate(BaseModel):
    """
    Request schema for batch recording of activity events.
    Sent by browser extension for batch synchronization.
    
    Browser extension provides raw event data for multiple events.
    Backend determines organization_id and user_id from JWT for each.
    """
    events: list[ActivityEventCreate] = Field(..., min_length=1, max_length=50, description="List of activity events to record (max 50)")

    @field_validator("events")
    @classmethod
    def validate_events_batch(cls, v: list[ActivityEventCreate]) -> list[ActivityEventCreate]:
        """Validate that batch size does not exceed maximum."""
        max_batch_size = settings.SESSION_BATCH_SIZE  # Reuse the same batch size setting
        if len(v) > max_batch_size:
            raise ValueError(f"Cannot upload more than {max_batch_size} events in a single batch")
        return v


class ActivityEventBatchResponse(BaseModel):
    """
    Response schema for batch activity event upload.
    Returns statistics about the batch processing.
    """
    inserted: int = Field(..., ge=0, description="Number of events successfully inserted")
    duplicates: int = Field(..., ge=0, description="Number of duplicate event_ids ignored")
    failed: int = Field(..., ge=0, description="Number of events that failed to insert")


class ActivityEventResponse(BaseModel):
    """
    Response schema for a single activity event.
    """
    id: int
    organization_id: int
    user_id: int
    event_id: str
    event_type: str
    browser_name: str
    tab_id: Optional[int]
    window_id: Optional[int]
    website_url: Optional[str]
    website_domain: Optional[str]
    page_title: Optional[str]
    previous_url: Optional[str]
    previous_domain: Optional[str]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
