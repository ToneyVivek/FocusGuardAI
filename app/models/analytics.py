from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Index
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
    )
