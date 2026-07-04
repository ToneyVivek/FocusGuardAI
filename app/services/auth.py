from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.core.security import get_password_hash, verify_password
from app.core.string_utils import normalize_email
from app.models.models import User, UserRole
from app.services.audit import create_audit_log

logger = get_logger(__name__)


def _get_active_user_by_email(db: Session, email: str) -> Optional[User]:
    normalized_email = normalize_email(email)
    return (
        db.query(User)
        .filter(User.email == normalized_email, User.is_deleted == False)
        .first()
    )


def _admin_exists(db: Session) -> bool:
    return (
        db.query(User.id)
        .filter(User.role == UserRole.ADMIN, User.is_deleted == False)
        .first()
        is not None
    )


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Retrieves user by email and validates their password, screening out soft-deleted users."""
    normalized_email = normalize_email(email)
    user = _get_active_user_by_email(db, normalized_email)
    
    if not user:
        create_audit_log(
            db=db,
            action="login_failed",
            metadata={"email": normalized_email, "reason": "user_not_found"},
        )
        return None
    
    if not verify_password(password, user.hashed_password):
        create_audit_log(
            db=db,
            action="login_failed",
            user_id=user.id,
            organization_id=user.organization_id,
            metadata={"email": normalized_email, "reason": "invalid_password"},
        )
        return None
    
    create_audit_log(
        db=db,
        action="login_success",
        user_id=user.id,
        organization_id=user.organization_id,
        metadata={"email": normalized_email},
    )
    
    return user


def register_bootstrap_admin(db: Session, email: str, full_name: str, password: str) -> User:
    """
    Registers the first platform admin.
    Subsequent admin accounts must be created through an invitation flow (future).
    """
    normalized_email = normalize_email(email)
    
    if _admin_exists(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is closed. The platform already has an administrator.",
        )

    if _get_active_user_by_email(db, normalized_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered.",
        )

    db_user = User(
        email=normalized_email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role=UserRole.ADMIN,
        organization_id=None,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info("Bootstrap admin registered: %s (ID: %s)", db_user.email, db_user.id)
    return db_user


def create_employee_user(
    db: Session,
    email: str,
    full_name: str,
    password: str,
    organization_id: int,
) -> User:
    """
    Internal service function — creates an employee linked to an organization.
    Only callable from the invitation onboarding flow, never from public registration.
    """
    normalized_email = normalize_email(email)
    
    if _get_active_user_by_email(db, normalized_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered.",
        )

    db_user = User(
        email=normalized_email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role=UserRole.EMPLOYEE,
        organization_id=organization_id,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(
        "Employee user created: %s (ID: %s, Org: %s)",
        db_user.email,
        db_user.id,
        organization_id,
    )
    return db_user
