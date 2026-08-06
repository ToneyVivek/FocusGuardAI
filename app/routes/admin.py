from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, status, Query
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_admin_with_org, get_db
from app.models.models import User, Invitation
from app.schemas.schemas import (
    InvitationCreate, 
    InvitationResponse, 
    UserResponse,
    EmployeeListResponse,
    EmployeeStatusUpdate,
    InvitationListResponse
)
from app.services.invitation import create_user_invitation
from app.services.employee import (
    get_organization_employees,
    get_employee_details,
    toggle_employee_status,
    remove_employee,
    get_pending_invitations,
    resend_invitation,
)

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.post("/invite-user", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def invite_user(
    invitation_in: InvitationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    Generates a secure onboarding token for an employee and sends an invitation link via email.
    Only accessible by ADMIN users who belong to an organization.
    """
    return create_user_invitation(
        db=db,
        email=invitation_in.email,
        organization_id=current_admin.organization_id,
        invited_by_id=current_admin.id,
        background_tasks=background_tasks,
    )


@router.get("/employees", response_model=EmployeeListResponse)
def list_employees(
    search: Optional[str] = Query(None, description="Search by name or email"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active or inactive"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    List all employees in the organization with optional search and filtering.
    Only accessible by ADMIN users who belong to an organization.
    """
    employees = get_organization_employees(
        db=db,
        organization_id=current_admin.organization_id,
        search=search,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    
    # Get total count for pagination
    from sqlalchemy import func
    total_query = (
        db.query(func.count(User.id))
        .filter(
            User.organization_id == current_admin.organization_id,
            User.is_deleted == False,
        )
    )
    
    if search:
        search_term = f"%{search}%"
        total_query = total_query.filter(
            (User.full_name.ilike(search_term)) | (User.email.ilike(search_term))
        )
    
    if status_filter == "active":
        total_query = total_query.filter(User.is_active == True)
    elif status_filter == "inactive":
        total_query = total_query.filter(User.is_active == False)
    
    total = total_query.scalar() or 0
    
    return EmployeeListResponse(
        employees=[UserResponse.model_validate(emp) for emp in employees],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/employees/{employee_id}", response_model=UserResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    Get details of a specific employee.
    Only accessible by ADMIN users who belong to the same organization.
    """
    employee = get_employee_details(
        db=db,
        organization_id=current_admin.organization_id,
        employee_id=employee_id,
    )
    return UserResponse.model_validate(employee)


@router.patch("/employees/{employee_id}/toggle-status", response_model=EmployeeStatusUpdate)
def toggle_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    Enable or disable an employee account.
    Only accessible by ADMIN users who belong to the same organization.
    Cannot be used on admin accounts.
    """
    employee = toggle_employee_status(
        db=db,
        organization_id=current_admin.organization_id,
        employee_id=employee_id,
        admin_id=current_admin.id,
    )
    return EmployeeStatusUpdate.model_validate(employee)


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    Remove an employee from the organization (soft delete).
    Only accessible by ADMIN users who belong to the same organization.
    Cannot be used on admin accounts.
    """
    remove_employee(
        db=db,
        organization_id=current_admin.organization_id,
        employee_id=employee_id,
        admin_id=current_admin.id,
    )


@router.get("/invitations", response_model=InvitationListResponse)
def list_invitations(
    limit: int = Query(100, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    List all pending invitations for the organization.
    Only accessible by ADMIN users who belong to the organization.
    """
    invitations = get_pending_invitations(
        db=db,
        organization_id=current_admin.organization_id,
        limit=limit,
        offset=offset,
    )
    
    # Get total count for pagination
    from sqlalchemy import func
    from datetime import datetime, timezone
    total = (
        db.query(func.count(Invitation.id))
        .filter(
            Invitation.organization_id == current_admin.organization_id,
            Invitation.is_used == False,
            Invitation.is_deleted == False,
            Invitation.expires_at > datetime.now(timezone.utc),
        )
        .scalar() or 0
    )
    
    return InvitationListResponse(
        invitations=[InvitationResponse.model_validate(inv) for inv in invitations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationResponse)
def resend_invitation_endpoint(
    invitation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    Resend an invitation email by generating a new token.
    Only accessible by ADMIN users who belong to the same organization.
    """
    invitation = resend_invitation(
        db=db,
        organization_id=current_admin.organization_id,
        invitation_id=invitation_id,
        admin_id=current_admin.id,
        background_tasks=background_tasks,
    )
    return InvitationResponse.model_validate(invitation)
