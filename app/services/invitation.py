import secrets

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.core.datetime_utils import ensure_utc_aware, utc_now, utc_now_plus
from app.core.logging_config import get_logger
from app.core.string_utils import normalize_email
from app.dependencies.deps import verify_tenant_access
from app.models.models import Invitation, Organization, User
from app.schemas.schemas import OnboardingSetup
from app.services.audit import create_audit_log
from app.services.auth import create_employee_user
from app.services.email import send_invitation_email

logger = get_logger(__name__)

INVITATION_EXPIRY_HOURS = 24


def create_user_invitation(
    db: Session,
    email: str,
    organization_id: int,
    invited_by_id: int,
    background_tasks: BackgroundTasks,
) -> Invitation:
    """
    Creates a secure registration token for a new employee, saves it,
    and registers the invitation email to be sent in the background.
    """
    normalized_email = normalize_email(email)
    
    inviter = (
        db.query(User)
        .filter(User.id == invited_by_id, User.is_deleted == False, User.is_active == True)
        .first()
    )
    if not inviter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inviter account is invalid or inactive.",
        )
    verify_tenant_access(inviter, organization_id)

    existing_user = (
        db.query(User)
        .filter(User.email == normalized_email, User.is_deleted == False)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address is already registered.",
        )

    org = (
        db.query(Organization)
        .filter(Organization.id == organization_id, Organization.is_deleted == False)
        .first()
    )
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or inactive.",
        )

    db.query(Invitation).filter(
        Invitation.email == normalized_email,
        Invitation.organization_id == organization_id,
        Invitation.is_used == False,
        Invitation.is_deleted == False,
    ).update({"is_deleted": True})
    db.commit()

    token = secrets.token_urlsafe(32)
    expires_at = utc_now_plus(hours=INVITATION_EXPIRY_HOURS)

    db_invite = Invitation(
        email=normalized_email,
        invitation_token=token,
        organization_id=organization_id,
        invited_by=invited_by_id,
        expires_at=expires_at,
        is_used=False,
    )

    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)

    background_tasks.add_task(
        send_invitation_email,
        to_email=normalized_email,
        org_name=org.organization_name,
        token=token,
    )

    create_audit_log(
        db=db,
        action="invitation_sent",
        user_id=invited_by_id,
        organization_id=organization_id,
        metadata={"email": normalized_email, "invitation_id": db_invite.id},
    )

    logger.info("User invitation queued for %s in organization %s", normalized_email, org.organization_name)
    return db_invite


def process_onboarding_setup(db: Session, setup_in: OnboardingSetup) -> User:
    """
    Validates the invitation token and, if successful, creates the user
    profile and marks the token as used.
    """
    invitation = (
        db.query(Invitation)
        .filter(Invitation.invitation_token == setup_in.token, Invitation.is_deleted == False)
        .first()
    )

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation token.",
        )

    if invitation.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation token has already been used.",
        )

    if ensure_utc_aware(invitation.expires_at) < utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation token has expired.",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == invitation.email, User.is_deleted == False)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email has already registered during the onboarding process.",
        )

    try:
        new_user = create_employee_user(
            db=db,
            email=invitation.email,
            full_name=setup_in.full_name,
            password=setup_in.password,
            organization_id=invitation.organization_id,
        )

        invitation.is_used = True
        db.add(invitation)
        db.commit()
        db.refresh(new_user)
        
        create_audit_log(
            db=db,
            action="onboarding_completed",
            user_id=new_user.id,
            organization_id=new_user.organization_id,
            metadata={"email": new_user.email, "invitation_id": invitation.id},
        )
        
        logger.info(
            "User %s onboarded to organization ID %s",
            new_user.email,
            invitation.organization_id,
        )
        return new_user
    except Exception:
        db.rollback()
        raise
