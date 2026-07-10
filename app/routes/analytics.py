from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_admin, get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.models.models import User
from app.schemas.analytics_schemas import BrowserActivityCreate, BrowserActivityResponse
from app.services.analytics_service import (
    get_organization_activities,
    get_user_activities,
    record_browser_activity,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post(
    "/activity",
    response_model=BrowserActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("100/minute")
def record_activity(
    request: Request,
    activity_in: BrowserActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Records a completed browser session.
    
    Called by browser extension when user switches tabs.
    The previous tab's session data is sent as a completed session.
    
    Browser extension ONLY provides raw browser data:
    - browser_name, website_url, website_domain, page_title
    - session_start_time, session_end_time
    
    Backend determines:
    - website_category (via classification service)
    - productivity_classification (via classification service)
    - duration_seconds (calculated from timestamps)
    - organization_id (from JWT, not client)
    - user_id (from JWT, not client)
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically extracted from authenticated user
    Rate Limiting: 100 requests per minute per IP
    """
    return record_browser_activity(db=db, activity_in=activity_in, user=current_user)


@router.get("/activity/my", response_model=list[BrowserActivityResponse])
@limiter.limit("60/minute")
def get_my_activities(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the authenticated user's browser activities.
    
    Returns activities from the user's organization only.
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    return get_user_activities(db=db, user=current_user, limit=limit, offset=offset)


@router.get("/activity/organization", response_model=list[BrowserActivityResponse])
@limiter.limit("60/minute")
def get_organization_activity(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Retrieves all browser activities for the admin's organization.
    
    Only accessible by organization admins.
    Returns activities across all users in the organization.
    """
    return get_organization_activities(db=db, user=current_admin, limit=limit, offset=offset)
