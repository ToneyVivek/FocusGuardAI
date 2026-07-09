import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
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
