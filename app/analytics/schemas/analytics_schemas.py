"""
Analytics schemas for FocusGuard.

Defines request and response schemas for analytics endpoints.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SummaryMetrics(BaseModel):
    """Summary metrics for analytics."""
    total_focus_time: int = Field(..., description="Total focus time in seconds")
    productive_time: int = Field(..., description="Productive time in seconds")
    neutral_time: int = Field(..., description="Neutral time in seconds")
    non_productive_time: int = Field(..., description="Non-productive time in seconds")
    idle_time: int = Field(..., description="Idle time in seconds")
    completed_sessions: int = Field(..., description="Number of completed browser sessions")
    idle_sessions: int = Field(..., description="Number of idle sessions")
    activity_events: int = Field(..., description="Number of activity events")


class ProductivityBreakdown(BaseModel):
    """Productivity breakdown by type."""
    productive: ProductivityType = Field(..., description="Productive time breakdown")
    neutral: ProductivityType = Field(..., description="Neutral time breakdown")
    non_productive: ProductivityType = Field(..., description="Non-productive time breakdown")


class ProductivityType(BaseModel):
    """Productivity type details."""
    duration_seconds: int = Field(..., description="Duration in seconds")
    percentage: float = Field(..., description="Percentage of total active time")


class CategoryBreakdownItem(BaseModel):
    """Category breakdown item."""
    category: str = Field(..., description="Website category")
    duration_seconds: int = Field(..., description="Total duration in seconds")
    percentage: float = Field(..., description="Percentage of total time")
    session_count: int = Field(..., description="Number of sessions")


class CategoryBreakdown(BaseModel):
    """Category breakdown."""
    categories: List[CategoryBreakdownItem] = Field(..., description="List of category breakdowns")


class DomainBreakdownItem(BaseModel):
    """Domain breakdown item."""
    domain: str = Field(..., description="Website domain")
    duration_seconds: int = Field(..., description="Total duration in seconds")
    session_count: int = Field(..., description="Number of sessions")


class DomainBreakdown(BaseModel):
    """Domain breakdown."""
    domains: List[DomainBreakdownItem] = Field(..., description="List of domain breakdowns")


class TimelineItem(BaseModel):
    """Timeline item."""
    session_id: int = Field(..., description="Session ID")
    start_time: datetime = Field(..., description="Session start time")
    end_time: datetime = Field(..., description="Session end time")
    duration_seconds: int = Field(..., description="Duration in seconds")
    website_url: Optional[str] = Field(None, description="Website URL")
    website_domain: Optional[str] = Field(None, description="Website domain")
    category: Optional[str] = Field(None, description="Website category")
    productivity: Optional[str] = Field(None, description="Productivity classification")


class Timeline(BaseModel):
    """Timeline data."""
    items: List[TimelineItem] = Field(..., description="Timeline items")


class FocusScore(BaseModel):
    """Focus score calculation."""
    score: float = Field(..., description="Focus score (0-100)")
    productive_time: int = Field(..., description="Productive time in seconds")
    total_active_time: int = Field(..., description="Total active time in seconds")


class UserSummaryResponseV2(BaseModel):
    """User summary response."""
    metrics: SummaryMetrics = Field(..., description="Summary metrics")
    productivity: ProductivityBreakdown = Field(..., description="Productivity breakdown")
    categories: CategoryBreakdown = Field(..., description="Category breakdown")
    domains: DomainBreakdown = Field(..., description="Domain breakdown")
    focus_score: FocusScore = Field(..., description="Focus score")


class OrganizationSummaryResponseV2(BaseModel):
    """Organization summary response."""
    metrics: SummaryMetrics = Field(..., description="Summary metrics")
    productivity: ProductivityBreakdown = Field(..., description="Productivity breakdown")
    categories: CategoryBreakdown = Field(..., description="Category breakdown")
    domains: DomainBreakdown = Field(..., description="Domain breakdown")
    employee_count: int = Field(..., description="Number of employees")


class EmployeeRankingItem(BaseModel):
    """Employee ranking item."""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    focus_score: float = Field(..., description="Focus score")
    productive_time: int = Field(..., description="Productive time in seconds")
    total_active_time: int = Field(..., description="Total active time in seconds")


class EmployeeRankings(BaseModel):
    """Employee rankings."""
    rankings: List[EmployeeRankingItem] = Field(..., description="Employee rankings")


class TrendDataPoint(BaseModel):
    """Trend data point."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    productive_time: int = Field(..., description="Productive time in seconds")
    total_active_time: int = Field(..., description="Total active time in seconds")
    focus_score: float = Field(..., description="Focus score for the day")


class Trends(BaseModel):
    """Trends data."""
    data_points: List[TrendDataPoint] = Field(..., description="Trend data points")
