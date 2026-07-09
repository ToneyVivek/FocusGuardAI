import logging

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analytics import BrowserActivity
from app.models.models import User
from app.schemas.analytics_schemas import BrowserActivityCreate, BrowserActivityResponse
from app.services.classification_service import classification_service

logger = logging.getLogger(__name__)


def record_browser_activity(
    db: Session,
    activity_in: BrowserActivityCreate,
    user: User,
) -> BrowserActivityResponse:
    """
    Records a completed browser session for analytics.
    
    This function is called when a user switches browser tabs.
    The previous tab's session is recorded as a completed session.
    
    Business logic moved to backend:
    - Classification: Backend determines category and productivity
    - Duration: Backend calculates duration from timestamps
    - Organization: Extracted from JWT, not from client
    
    Transaction flow:
    1. Validate user belongs to an organization
    2. Classify website (backend determines category/productivity)
    3. Calculate duration (backend computes from timestamps)
    4. Create browser activity record
    5. Commit transaction
    6. Return recorded activity
    
    Args:
        db: Database session
        activity_in: Browser activity data from extension (raw data only)
        user: Authenticated user (from JWT token)
        
    Returns:
        Recorded browser activity
        
    Raises:
        HTTPException: If user has no organization
    """
    # Ensure user belongs to an organization
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to record activity.",
        )
    
    # Classify website (backend business logic)
    website_category, productivity_classification = classification_service.classify_website(
        activity_in.website_domain
    )
    
    # Calculate duration (backend business logic)
    duration_seconds = int(
        (activity_in.session_end_time - activity_in.session_start_time).total_seconds()
    )
    
    # Validate duration is positive
    if duration_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session duration: session_end_time must be after session_start_time",
        )
    
    # Create browser activity record
    db_activity = BrowserActivity(
        organization_id=user.organization_id,  # From JWT, not client
        user_id=user.id,  # From JWT, not client
        username=user.full_name,  # Denormalized for reporting
        browser_name=activity_in.browser_name,
        website_url=activity_in.website_url,
        website_domain=activity_in.website_domain,
        page_title=activity_in.page_title,
        website_category=website_category,  # Backend-determined
        productivity_classification=productivity_classification,  # Backend-determined
        session_start_time=activity_in.session_start_time,
        session_end_time=activity_in.session_end_time,
        duration_seconds=duration_seconds,  # Backend-calculated
    )
    
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    logger.info(
        "Browser activity recorded: user_id=%s, org_id=%s, domain=%s, category=%s, productivity=%s, duration=%s",
        user.id,
        user.organization_id,
        activity_in.website_domain,
        website_category,
        productivity_classification,
        duration_seconds,
    )
    
    return BrowserActivityResponse.model_validate(db_activity)


def get_user_activities(
    db: Session,
    user: User,
    limit: int = 100,
    offset: int = 0,
) -> list[BrowserActivityResponse]:
    """
    Retrieves browser activities for the authenticated user.
    
    Organization-aware: Only returns activities from user's organization.
    
    Args:
        db: Database session
        user: Authenticated user
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of browser activities
    """
    if user.organization_id is None:
        return []
    
    activities = (
        db.query(BrowserActivity)
        .filter(
            BrowserActivity.organization_id == user.organization_id,
            BrowserActivity.user_id == user.id,
        )
        .order_by(BrowserActivity.session_start_time.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return [BrowserActivityResponse.model_validate(activity) for activity in activities]


def get_organization_activities(
    db: Session,
    user: User,
    limit: int = 100,
    offset: int = 0,
) -> list[BrowserActivityResponse]:
    """
    Retrieves browser activities for the user's organization.
    
    Only accessible by admins. Returns all activities across the organization.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of browser activities for the organization
    """
    if user.organization_id is None:
        return []
    
    activities = (
        db.query(BrowserActivity)
        .filter(BrowserActivity.organization_id == user.organization_id)
        .order_by(BrowserActivity.session_start_time.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return [BrowserActivityResponse.model_validate(activity) for activity in activities]
