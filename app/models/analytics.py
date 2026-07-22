from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Index, JSON
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.models import (
    TimestampMixin,
    WebsiteCategory,
    ProductivityClassification,
)


class BrowserActivity(Base, TimestampMixin):
    """
    Stores completed browser session data for analytics.
    One record per completed browser session (not per second).
    """
    __tablename__ = "browser_activities"

    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant isolation
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username = Column(String(255), nullable=True, index=True)  # Denormalized for reporting
    
    # Browser and website information
    browser_name = Column(String(100), nullable=False)  # e.g., "Chrome", "Firefox"
    website_url = Column(String(2048), nullable=False)
    website_domain = Column(String(255), nullable=False, index=True)
    page_title = Column(String(500), nullable=True)
    
    # Categorization
    website_category = Column(
        SQLEnum(WebsiteCategory),
        nullable=False,
        default=WebsiteCategory.OTHER,
        index=True,
    )
    productivity_classification = Column(
        SQLEnum(ProductivityClassification),
        nullable=False,
        default=ProductivityClassification.NEUTRAL,
        index=True,
    )
    
    # Session timing
    session_start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    session_end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        # Organization + user filtering (most common)
        Index("idx_org_user_time", "organization_id", "user_id", "session_start_time"),
        # Organization + category filtering (reporting)
        Index("idx_org_category_time", "organization_id", "website_category", "session_start_time"),
        # Organization + productivity filtering (reporting)
        Index("idx_org_productivity_time", "organization_id", "productivity_classification", "session_start_time"),
        # Domain-based analytics
        Index("idx_org_domain_time", "organization_id", "website_domain", "session_start_time"),
        # Time-range queries
        Index("idx_org_time_range", "organization_id", "session_start_time", "session_end_time"),
        # Unique constraint for duplicate prevention (idempotency)
        # Prevents duplicate records for same user, domain, and time range
        Index("idx_unique_session", "user_id", "website_domain", "session_start_time", "session_end_time", unique=True),
    )


class ActivityEvent(Base, TimestampMixin):
    """
    Stores individual browser activity events for detailed analytics.
    One record per event (tab change, window focus, etc.).
    """
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant isolation
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event identification
    event_id = Column(String(100), nullable=False, unique=True, index=True)  # Extension UUID for idempotency
    event_type = Column(String(50), nullable=False, index=True)  # TAB_CREATED, TAB_ACTIVATED, etc.

    # Browser context
    browser_name = Column(String(100), nullable=False)

    # Tab/window context (nullable for lifecycle events)
    tab_id = Column(Integer, nullable=True, index=True)
    window_id = Column(Integer, nullable=True, index=True)

    # Website context (nullable for non-tab events)
    website_url = Column(String(2048), nullable=True)
    website_domain = Column(String(255), nullable=True, index=True)
    page_title = Column(String(500), nullable=True)

    # Navigation context (for tab updates)
    previous_url = Column(String(2048), nullable=True)
    previous_domain = Column(String(255), nullable=True)

    # Event timing
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Additional event metadata (flexible JSON for future extensibility)
    event_metadata = Column(JSON, nullable=True)

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")

    # Composite indexes for common query patterns
    __table_args__ = (
        # Organization + user + time filtering (most common)
        Index("idx_activity_org_user_time", "organization_id", "user_id", "timestamp"),
        # Organization + event type filtering
        Index("idx_activity_org_type_time", "organization_id", "event_type", "timestamp"),
        # Tab-based timeline queries
        Index("idx_activity_tab_time", "user_id", "tab_id", "timestamp"),
        # Window-based timeline queries
        Index("idx_activity_window_time", "user_id", "window_id", "timestamp"),
        # Domain-based event analytics
        Index("idx_activity_domain_time", "organization_id", "website_domain", "timestamp"),
    )
