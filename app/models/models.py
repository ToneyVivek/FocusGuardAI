import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, LargeBinary, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"


class WebsiteCategory(str, enum.Enum):
    """Centralized website categorization system."""
    DEVELOPMENT = "DEVELOPMENT"
    EDUCATION = "EDUCATION"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    ENTERTAINMENT = "ENTERTAINMENT"
    PRODUCTIVITY = "PRODUCTIVITY"
    COMMUNICATION = "COMMUNICATION"
    AI_TOOL = "AI_TOOL"
    NEWS = "NEWS"
    SEARCH_ENGINE = "SEARCH_ENGINE"
    SHOPPING = "SHOPPING"
    OTHER = "OTHER"


class ProductivityClassification(str, enum.Enum):
    """Productivity classification independent of category."""
    PRODUCTIVE = "PRODUCTIVE"
    NON_PRODUCTIVE = "NON_PRODUCTIVE"
    NEUTRAL = "NEUTRAL"


class TimestampMixin:
    """Mixin to inject timezone-aware UTC created_at and updated_at datetime stamps."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin to inject soft deletion attributes and helper functionality."""

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def soft_delete(self, db):
        """Soft-deletes the record by setting is_deleted=True and tracking time.
        
        IMPORTANT: This method does NOT commit. The caller must handle transaction lifecycle.
        """
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        db.add(self)
        db.flush()


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    organization = relationship("Organization", back_populates="users")
    sent_invitations = relationship(
        "Invitation",
        back_populates="sender",
        foreign_keys="[Invitation.invited_by]",
    )


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", back_populates="organization")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")

    @property
    def name(self) -> str:
        """Alias for organization_name for API responses."""
        return self.organization_name


class Invitation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    invitation_token = Column(String, unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", back_populates="invitations")
    sender = relationship("User", back_populates="sent_invitations", foreign_keys=[invited_by])


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    audit_metadata = Column(Text, nullable=True)

    organization = relationship("Organization")
    user = relationship("User")


class RefreshToken(Base, TimestampMixin):
    """
    Refresh tokens for JWT access token renewal.
    
    Security:
    - Only stores SHA-256 hash of the token, never the raw token
    - Tokens are rotated on each refresh (old token invalidated)
    - Tokens have configurable expiration (default 7 days)
    - Tokens can be revoked via logout
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(LargeBinary(32), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="refresh_tokens")

    __table_args__ = (
        # Index for efficient lookup of active tokens
        Index("idx_refresh_tokens_active", "user_id", "is_revoked", "expires_at"),
    )


class IdleSession(Base, TimestampMixin):
    """
    Idle session tracking for user inactivity periods.
    
    Tracks periods where the user was idle (no browser activity).
    Duration is calculated from timestamps by the backend.
    """
    __tablename__ = "idle_sessions"

    id = Column(Integer, primary_key=True, index=True)
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
    idle_start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    idle_end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=False)

    organization = relationship("Organization")
    user = relationship("User")

    __table_args__ = (
        # Index for efficient querying by user and time range
        Index("idx_idle_sessions_user_time", "user_id", "idle_start_time", "idle_end_time"),
        # Index for organization-level analytics
        Index("idx_idle_sessions_org_time", "organization_id", "idle_start_time"),
    )


class AIReportCache(Base, TimestampMixin):
    """
    Cache for AI-generated Daily and Weekly summaries.
    
    Stores generated summaries to avoid redundant AI calls when analytics haven't changed.
    Cache is invalidated automatically when analytics hash, provider, model, or prompt version changes.
    """
    __tablename__ = "ai_report_cache"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_type = Column(String(20), nullable=False, index=True)  # "daily" or "weekly"
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    analytics_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash of analytics data
    
    # Cache versioning fields
    provider = Column(String(50), nullable=False, index=True)  # "gemini", "grok", "openai"
    model = Column(String(100), nullable=False, index=True)  # "gemini-flash-latest", etc.
    prompt_version = Column(String(20), nullable=False, index=True)  # "7.5", etc.
    
    # Structured storage
    raw_llm_response = Column(Text, nullable=False)  # Raw response from LLM
    parsed_summary = Column(JSON, nullable=False)  # Parsed summary response
    cache_metadata = Column(JSON, nullable=False)  # Generation metadata
    
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    user = relationship("User", backref="ai_report_cache")

    __table_args__ = (
        # Composite index for efficient cache lookup
        Index(
            "idx_ai_cache_lookup",
            "user_id",
            "report_type",
            "start_date",
            "end_date",
            "analytics_hash",
            "provider",
            "model",
            "prompt_version",
            unique=True
        ),
        # Index for cleanup of expired entries
        Index("idx_ai_cache_expires", "expires_at"),
    )


class AIConversation(Base, TimestampMixin):
    """
    AI Chat Conversation persistence.
    
    Stores conversation history for AI chat sessions to enable
    conversation restoration after page refresh.
    """
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    messages = Column(JSON, nullable=False, default=list)  # List of {role, content, timestamp}
    suggested_questions = Column(JSON, nullable=True)  # List of suggested questions
    last_message_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", backref="ai_conversations")

    __table_args__ = (
        Index("idx_ai_conversations_user_last_message", "user_id", "last_message_at"),
    )
