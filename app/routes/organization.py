from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_admin, get_db
from app.models.models import User
from app.schemas.schemas import OrganizationCreate, OrganizationResponse
from app.services.organization import create_organization_with_admin

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/create", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_org(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Creates a new organization and links the creating admin in a single transaction.
    Only accessible to ADMIN users without an existing organization.
    """
    return create_organization_with_admin(db=db, org_in=org_in, admin=current_admin)
