from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_admin_with_org, get_db
from app.models.models import User
from app.schemas.schemas import InvitationCreate, InvitationResponse
from app.services.invitation import create_user_invitation

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
