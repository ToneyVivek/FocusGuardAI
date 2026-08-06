"""
Employee management service for organization admins.

Features:
- List employees with search and filtering
- Get employee details
- Enable/disable employee accounts
- Remove employees (soft delete)
- List pending invitations
- Resend invitations
- Multi-tenant isolation
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.config.config import settings
from app.models.models import User, Invitation, UserRole
from app.schemas.schemas import UserResponse, InvitationResponse
from app.services.audit import create_audit_log
from app.services.email import send_invitation_email
from app.core.string_utils import normalize_email

logger = logging.getLogger(__name__)

INVITATION_EXPIRY_HOURS = 24


def get_organization_employees(
    db: Session,
    organization_id: int,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[User]:
    """
    Get list of employees in an organization with optional search and filtering.
    
    Args:
        db: Database session
        organization_id: Organization ID
        search: Optional search term for name or email
        status_filter: Optional filter by status ('active', 'inactive')
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of users
    """
    query = (
        db.query(User)
        .filter(
            User.organization_id == organization_id,
            User.is_deleted == False,
        )
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) | (User.email.ilike(search_term))
        )
    
    # Apply status filter
    if status_filter == "active":
        query = query.filter(User.is_active == True)
    elif status_filter == "inactive":
        query = query.filter(User.is_active == False)
    
    # Order by created_at descending (newest first)
    query = query.order_by(User.created_at.desc())
    
    # Apply pagination
    employees = query.limit(limit).offset(offset).all()
    
    return employees


def get_employee_details(
    db: Session,
    organization_id: int,
    employee_id: int,
) -> User:
    """
    Get details of a specific employee.
    
    Args:
        db: Database session
        organization_id: Organization ID (for tenant isolation)
        employee_id: User ID to fetch
        
    Returns:
        User object
        
    Raises:
        HTTPException: If employee not found or not in organization
    """
    employee = (
        db.query(User)
        .filter(
            User.id == employee_id,
            User.organization_id == organization_id,
            User.is_deleted == False,
        )
        .first()
    )
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee


def toggle_employee_status(
    db: Session,
    organization_id: int,
    employee_id: int,
    admin_id: int,
) -> User:
    """
    Enable or disable an employee account.
    
    Args:
        db: Database session
        organization_id: Organization ID (for tenant isolation)
        employee_id: User ID to toggle
        admin_id: ID of admin performing the action
        
    Returns:
        Updated user object
        
    Raises:
        HTTPException: If employee not found, not in organization, or is admin
    """
    employee = (
        db.query(User)
        .filter(
            User.id == employee_id,
            User.organization_id == organization_id,
            User.is_deleted == False,
        )
        .first()
    )
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Prevent disabling the last admin
    if employee.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable admin accounts through this endpoint"
        )
    
    # Toggle status
    employee.is_active = not employee.is_active
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    # Audit log
    try:
        create_audit_log(
            db=db,
            action="employee_status_toggled",
            user_id=admin_id,
            organization_id=organization_id,
            metadata={
                "employee_id": employee_id,
                "new_status": employee.is_active,
                "employee_email": employee.email,
            },
        )
        db.commit()
    except Exception as e:
        logger.error(f"Failed to create audit log for employee status toggle: {e}")
    
    logger.info(
        f"Employee status toggled: employee_id={employee_id}, "
        f"new_status={employee.is_active}, by_admin={admin_id}"
    )
    
    return employee


def remove_employee(
    db: Session,
    organization_id: int,
    employee_id: int,
    admin_id: int,
) -> None:
    """
    Remove an employee from the organization (soft delete).
    
    Args:
        db: Database session
        organization_id: Organization ID (for tenant isolation)
        employee_id: User ID to remove
        admin_id: ID of admin performing the action
        
    Raises:
        HTTPException: If employee not found, not in organization, or is admin
    """
    employee = (
        db.query(User)
        .filter(
            User.id == employee_id,
            User.organization_id == organization_id,
            User.is_deleted == False,
        )
        .first()
    )
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Prevent removing the last admin
    if employee.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin accounts through this endpoint"
        )
    
    # Soft delete
    employee.soft_delete(db)
    db.commit()
    
    # Audit log
    try:
        create_audit_log(
            db=db,
            action="employee_removed",
            user_id=admin_id,
            organization_id=organization_id,
            metadata={
                "employee_id": employee_id,
                "employee_email": employee.email,
                "employee_name": employee.full_name,
            },
        )
        db.commit()
    except Exception as e:
        logger.error(f"Failed to create audit log for employee removal: {e}")
    
    logger.info(
        f"Employee removed: employee_id={employee_id}, "
        f"email={employee.email}, by_admin={admin_id}"
    )


def get_pending_invitations(
    db: Session,
    organization_id: int,
    limit: int = 100,
    offset: int = 0,
) -> List[Invitation]:
    """
    Get list of pending invitations for an organization.
    
    Args:
        db: Database session
        organization_id: Organization ID
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of invitations
    """
    invitations = (
        db.query(Invitation)
        .filter(
            Invitation.organization_id == organization_id,
            Invitation.is_used == False,
            Invitation.is_deleted == False,
            Invitation.expires_at > datetime.now(timezone.utc),
        )
        .order_by(Invitation.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return invitations


def resend_invitation(
    db: Session,
    organization_id: int,
    invitation_id: int,
    admin_id: int,
    background_tasks: BackgroundTasks,
) -> Invitation:
    """
    Resend an invitation email by updating the token and expiry.
    
    Args:
        db: Database session
        organization_id: Organization ID (for tenant isolation)
        invitation_id: Invitation ID to resend
        admin_id: ID of admin performing the action
        background_tasks: FastAPI background tasks
        
    Returns:
        Updated invitation object
        
    Raises:
        HTTPException: If invitation not found, already used, or not in organization
    """
    import secrets
    
    invitation = (
        db.query(Invitation)
        .filter(
            Invitation.id == invitation_id,
            Invitation.organization_id == organization_id,
            Invitation.is_deleted == False,
        )
        .first()
    )
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been used"
        )
    
    # Generate new token and expiry
    new_token = secrets.token_urlsafe(32)
    new_expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITATION_EXPIRY_HOURS)
    
    invitation.invitation_token = new_token
    invitation.expires_at = new_expires_at
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    # Send email in background
    from app.models.models import Organization
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    background_tasks.add_task(
        send_invitation_email,
        to_email=invitation.email,
        org_name=org.organization_name if org else "Organization",
        token=new_token,
    )
    
    # Audit log
    try:
        create_audit_log(
            db=db,
            action="invitation_resent",
            user_id=admin_id,
            organization_id=organization_id,
            metadata={
                "invitation_id": invitation_id,
                "email": invitation.email,
            },
        )
        db.commit()
    except Exception as e:
        logger.error(f"Failed to create audit log for invitation resend: {e}")
    
    logger.info(
        f"Invitation resent: invitation_id={invitation_id}, "
        f"email={invitation.email}, by_admin={admin_id}"
    )
    
    return invitation
