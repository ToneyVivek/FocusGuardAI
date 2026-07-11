from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import logging
from app.models.models import Organization, User
from app.schemas.schemas import OrganizationCreate
from app.services.audit import create_audit_log

logger = logging.getLogger(__name__)


def create_organization_with_admin(
    db: Session,
    org_in: OrganizationCreate,
    admin: User,
) -> Organization:
    """
    Creates a new organization and links the admin in a single transaction.
    """
    if admin.organization_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already associated with an organization.",
        )

    existing_org = (
        db.query(Organization)
        .filter(
            func.lower(Organization.organization_name) == org_in.organization_name.lower(),
            Organization.is_deleted == False,
        )
        .first()
    )

    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization with this name already exists.",
        )

    try:
        db_org = Organization(organization_name=org_in.organization_name)
        db.add(db_org)
        db.flush()

        admin.organization_id = db_org.id
        db.add(admin)
        db.commit()
        db.refresh(db_org)
        
        try:
            create_audit_log(
                db=db,
                action="organization_created",
                user_id=admin.id,
                organization_id=db_org.id,
                metadata={"organization_name": db_org.organization_name},
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to create audit log for organization creation: {e}")
        
        logger.info(
            "Organization created and admin linked: %s (ID: %s, Admin: %s)",
            db_org.organization_name,
            db_org.id,
            admin.id,
        )
        return db_org
    except Exception:
        db.rollback()
        raise
