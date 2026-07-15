"""
Pydantic schemas for idle session tracking.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IdleSessionCreate(BaseModel):
    """Request schema for creating an idle session."""
    idle_start_time: datetime = Field(..., description="When the idle period started")
    idle_end_time: datetime = Field(..., description="When the idle period ended")

    @field_validator("idle_end_time")
    @classmethod
    def validate_idle_timing(cls, v: datetime, info) -> datetime:
        """Validate that end_time is after start_time."""
        if "idle_start_time" in info.data:
            start_time = info.data["idle_start_time"]
            if v <= start_time:
                raise ValueError("idle_end_time must be after idle_start_time")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idle_start_time": "2026-07-15T10:00:00Z",
                "idle_end_time": "2026-07-15T10:05:30Z",
            }
        }
    )


class IdleSessionResponse(BaseModel):
    """Response schema for idle session data."""
    id: int
    organization_id: int
    user_id: int
    idle_start_time: datetime
    idle_end_time: datetime
    duration_seconds: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "organization_id": 1,
                "user_id": 1,
                "idle_start_time": "2026-07-15T10:00:00Z",
                "idle_end_time": "2026-07-15T10:05:30Z",
                "duration_seconds": 330,
                "created_at": "2026-07-15T10:05:35Z",
                "updated_at": "2026-07-15T10:05:35Z",
            }
        }
    )
