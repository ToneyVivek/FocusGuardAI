from typing import Optional
from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_admin_with_org, get_db
from app.models.models import User, Invitation, AIReportCache
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
from app.services.pdf_report_service import generate_employee_report_pdf

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


@router.get("/organization/reports")
def list_organization_reports(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    List all AI-generated reports for the organization.
    Returns cached reports with user information.
    Only accessible by ADMIN users.
    """
    if current_admin.organization_id is None:
        return []
    
    # Get all users in the organization
    user_ids = (
        db.query(User.id)
        .filter(User.organization_id == current_admin.organization_id)
        .all()
    )
    user_id_list = [uid[0] for uid in user_ids]
    
    # Get all cached reports for these users
    reports = (
        db.query(AIReportCache, User)
        .join(User, AIReportCache.user_id == User.id)
        .filter(AIReportCache.user_id.in_(user_id_list))
        .order_by(AIReportCache.created_at.desc())
        .all()
    )
    
    result = []
    for report, user in reports:
        result.append({
            "id": report.id,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "start_date": report.start_date.isoformat(),
            "end_date": report.end_date.isoformat(),
            "created_at": report.created_at.isoformat(),
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
            }
        })
    
    return result


@router.get("/employee/{employee_id}/reports")
def list_employee_reports(
    employee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    List all AI-generated reports for a specific employee.
    Only accessible by ADMIN users in the same organization.
    """
    if current_admin.organization_id is None:
        return []
    
    # Verify the employee belongs to the same organization
    employee = db.query(User).filter(
        User.id == employee_id,
        User.organization_id == current_admin.organization_id
    ).first()
    
    if not employee:
        return []
    
    # Get all cached reports for this employee
    reports = (
        db.query(AIReportCache)
        .filter(AIReportCache.user_id == employee_id)
        .order_by(AIReportCache.created_at.desc())
        .all()
    )
    
    result = []
    for report in reports:
        result.append({
            "id": report.id,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "start_date": report.start_date.isoformat(),
            "end_date": report.end_date.isoformat(),
            "created_at": report.created_at.isoformat(),
        })
    
    return result


@router.get("/employee/{employee_id}/report/pdf")
def download_employee_report_pdf(
    employee_id: int,
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    Generate and download a PDF report for an employee's productivity analytics.
    Only accessible by ADMIN users in the same organization.
    """
    if current_admin.organization_id is None:
        return None
    
    # Prevent PDF generation for incomplete "Today" reports
    from datetime import datetime
    today = date.today()
    if start_date == today and end_date == today:
        return Response(
            content='{"error": "Today\'s report is still being generated. Please download the report tomorrow or choose another completed date range."}',
            media_type="application/json",
            status_code=400
        )
    
    # Verify the employee belongs to the same organization
    employee = db.query(User).filter(
        User.id == employee_id,
        User.organization_id == current_admin.organization_id
    ).first()
    
    if not employee:
        return None
    
    # Generate PDF
    pdf_buffer = generate_employee_report_pdf(db, employee, start_date, end_date)
    
    # Return PDF as response
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=productivity_report_{employee.full_name.replace(' ', '_')}_{start_date}_to_{end_date}.pdf"
        }
    )


@router.get("/employee/{employee_id}")
def get_employee_profile(
    employee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_with_org),
):
    """
    Get detailed profile information for a specific employee.
    Only accessible by ADMIN users in the same organization.
    """
    if current_admin.organization_id is None:
        return None
    
    # Verify the employee belongs to the same organization
    employee = db.query(User).filter(
        User.id == employee_id,
        User.organization_id == current_admin.organization_id
    ).first()
    
    if not employee:
        return None
    
    from app.models.models import Organization
    
    # Get organization details
    organization = db.query(Organization).filter(
        Organization.id == employee.organization_id
    ).first()
    
    # Note: BrowserActivity and ActivityEvent models don't exist in the current codebase
    # Last activity calculation will be implemented when these models are available
    last_activity = None
    
    return {
        "id": employee.id,
        "email": employee.email,
        "full_name": employee.full_name,
        "role": employee.role,
        "is_active": employee.is_active,
        "created_at": employee.created_at.isoformat(),
        "updated_at": employee.updated_at.isoformat(),
        "last_activity": last_activity,
        "organization_id": employee.organization_id,
        "organization": {
            "id": organization.id if organization else None,
            "name": organization.name if organization else None,
        } if organization else None,
    }
