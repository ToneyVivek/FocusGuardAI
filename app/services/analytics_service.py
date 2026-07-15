import logging

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, distinct, desc, case, literal_column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.analytics import BrowserActivity
from app.models.models import User, WebsiteCategory, ProductivityClassification, IdleSession
from app.schemas.analytics_schemas import (
    BrowserActivityCreate, 
    BrowserActivityResponse,
    UnifiedTimelineItem
)
from app.services.audit import create_audit_log
from app.services.classification_service import classification_service
from app.services.domain_normalization import domain_normalization_service
from app.services.duplicate_detection import duplicate_detection_service

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
    # Domain is already normalized by schema validation
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
    
    try:
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
    except IntegrityError as db_error:
        # Rollback the failed transaction to reset session state
        db.rollback()
        
        # Check if this is a unique constraint violation (duplicate activity)
        if duplicate_detection_service.is_duplicate_error(db_error):
            # Idempotent: Return existing record instead of failing
            logger.info(
                "Duplicate activity detected, checking for existing record: user_id=%s, domain=%s",
                user.id,
                activity_in.website_domain,
            )
            existing_activity = duplicate_detection_service.check_duplicate(
                db=db,
                user_id=user.id,
                website_domain=activity_in.website_domain,
                session_start_time=activity_in.session_start_time,
                session_end_time=activity_in.session_end_time,
            )
            if existing_activity:
                return BrowserActivityResponse.model_validate(existing_activity)
        
        # Re-raise if not a duplicate error
        raise db_error
    
    # Audit logging (non-blocking)
    try:
        create_audit_log(
            db=db,
            action="browser_activity_recorded",
            user_id=user.id,
            organization_id=user.organization_id,
            metadata={
                "domain": activity_in.website_domain,
                "category": str(website_category),
                "productivity": str(productivity_classification),
                "duration": duration_seconds,
            },
        )
        db.commit()  # Commit audit log separately
    except Exception as audit_error:
        # Audit logging failure should never crash the main request
        logger.error(f"Audit logging failed for browser activity: {audit_error}", exc_info=True)
        # Continue normally - activity was already recorded successfully
    
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


def format_seconds_to_hhmmss(seconds: int) -> str:
    """Helper to format duration in seconds as HH:MM:SS string."""
    if seconds is None or seconds < 0:
        return "00:00:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_friendly_website_name(domain: str) -> str:
    """Helper to map normalized domain to a friendly display name."""
    mapping = {
        "github.com": "GitHub",
        "chat.openai.com": "ChatGPT",
        "openai.com": "OpenAI",
        "claude.ai": "Claude",
        "google.com": "Google",
        "youtube.com": "YouTube",
        "facebook.com": "Facebook",
        "linkedin.com": "LinkedIn",
        "slack.com": "Slack",
        "twitter.com": "Twitter",
        "x.com": "X",
    }
    normalized = domain.lower().strip()
    if normalized in mapping:
        return mapping[normalized]
    
    parts = normalized.split('.')
    if len(parts) >= 2:
        if parts[0] in ("www", "mail", "api", "m"):
            name = parts[1]
        else:
            name = parts[-2]
    else:
        name = normalized
    
    return name.capitalize()


def compute_percentage(duration_seconds: int, total_time_seconds: int) -> float:
    """Return duration share of total time, rounded to two decimal places."""
    if not total_time_seconds:
        return 0.0
    return round((duration_seconds / total_time_seconds) * 100, 2)


def get_user_analytics_summary(db: Session, user: User) -> dict:
    """
    Computes an aggregated productivity and activity summary for the user.
    Calculations are performed on-demand directly via database aggregation.
    Includes both browser activity and idle session data.
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics summary."
        )

    # 1. Total statistics (browser activity)
    totals = (
        db.query(
            func.sum(BrowserActivity.duration_seconds).label("total_time"),
            func.count(BrowserActivity.id).label("total_tab_switches"),
            func.count(distinct(BrowserActivity.website_domain)).label("total_websites"),
            func.max(BrowserActivity.session_end_time).label("last_activity_at"),
        )
        .filter(
            BrowserActivity.user_id == user.id,
            BrowserActivity.organization_id == user.organization_id
        )
        .first()
    )

    total_browser_time_seconds = getattr(totals, "total_time", 0) or 0
    total_tab_switches = getattr(totals, "total_tab_switches", 0) or 0
    total_websites_visited = getattr(totals, "total_websites", 0) or 0
    last_activity_at = getattr(totals, "last_activity_at", None)

    # 2. Idle session statistics
    idle_totals = (
        db.query(
            func.sum(IdleSession.duration_seconds).label("total_idle_time"),
            func.count(IdleSession.id).label("idle_sessions_count"),
        )
        .filter(
            IdleSession.user_id == user.id,
            IdleSession.organization_id == user.organization_id
        )
        .first()
    )

    total_idle_time_seconds = getattr(idle_totals, "total_idle_time", 0) or 0
    idle_sessions_count = getattr(idle_totals, "idle_sessions_count", 0) or 0

    # 3. Calculate combined totals
    total_logged_time_seconds = total_browser_time_seconds + total_idle_time_seconds

    # 2. Time spent per productivity classification
    prod_query = (
        db.query(
            BrowserActivity.productivity_classification,
            func.sum(BrowserActivity.duration_seconds).label("duration")
        )
        .filter(
            BrowserActivity.user_id == user.id,
            BrowserActivity.organization_id == user.organization_id
        )
        .group_by(BrowserActivity.productivity_classification)
        .all()
    )

    productive_seconds = 0
    non_productive_seconds = 0
    neutral_seconds = 0

    for classification, duration in prod_query:
        if classification == ProductivityClassification.PRODUCTIVE:
            productive_seconds = duration or 0
        elif classification == ProductivityClassification.NON_PRODUCTIVE:
            non_productive_seconds = duration or 0
        elif classification == ProductivityClassification.NEUTRAL:
            neutral_seconds = duration or 0

    # 4. Category Summary
    cat_query = (
        db.query(
            BrowserActivity.website_category,
            func.sum(BrowserActivity.duration_seconds).label("duration")
        )
        .filter(
            BrowserActivity.user_id == user.id,
            BrowserActivity.organization_id == user.organization_id
        )
        .group_by(BrowserActivity.website_category)
        .all()
    )

    CATEGORY_DISPLAY_NAMES = {
        WebsiteCategory.DEVELOPMENT: "Development",
        WebsiteCategory.AI_TOOL: "AI Tool",
        WebsiteCategory.COMMUNICATION: "Communication",
        WebsiteCategory.ENTERTAINMENT: "Entertainment",
        WebsiteCategory.SOCIAL_MEDIA: "Social Media",
        WebsiteCategory.PRODUCTIVITY: "Productivity",
        WebsiteCategory.OTHER: "Other",
        WebsiteCategory.EDUCATION: "Education",
        WebsiteCategory.NEWS: "News",
        WebsiteCategory.SEARCH_ENGINE: "Search Engine",
        WebsiteCategory.SHOPPING: "Shopping",
    }

    category_summary = []
    for category, duration in cat_query:
        if duration and duration > 0:
            display_name = CATEGORY_DISPLAY_NAMES.get(category, str(category).replace("_", " ").title())
            category_summary.append({
                "category": display_name,
                "time_spent": format_seconds_to_hhmmss(duration),
                "duration_seconds": duration,
                "percentage": compute_percentage(duration, total_browser_time_seconds),
            })
    category_summary.sort(key=lambda item: item["duration_seconds"], reverse=True)

    # 5. Website Summary
    web_query = (
        db.query(
            BrowserActivity.website_domain,
            func.min(BrowserActivity.website_url).label("url"),
            func.sum(BrowserActivity.duration_seconds).label("duration"),
            func.count(BrowserActivity.id).label("visits")
        )
        .filter(
            BrowserActivity.user_id == user.id,
            BrowserActivity.organization_id == user.organization_id
        )
        .group_by(BrowserActivity.website_domain)
        .order_by(desc("duration"))
        .all()
    )

    website_summary = []
    for domain, url, duration, visits in web_query:
        if not duration or duration <= 0:
            continue
        website_summary.append({
            "name": get_friendly_website_name(domain),
            "domain": domain,
            "url": url,
            "time_spent": format_seconds_to_hhmmss(duration),
            "duration_seconds": duration,
            "visits": visits or 0,
            "percentage": compute_percentage(duration, total_browser_time_seconds),
        })

    return {
        "user": {
            "id": user.id,
            "username": user.full_name,
            "email": user.email
        },
        "productive_time": format_seconds_to_hhmmss(productive_seconds),
        "non_productive_time": format_seconds_to_hhmmss(non_productive_seconds),
        "neutral_time": format_seconds_to_hhmmss(neutral_seconds),
        "total_websites_visited": total_websites_visited,
        "total_tab_switches": total_tab_switches,
        "total_time": format_seconds_to_hhmmss(total_browser_time_seconds),
        "idle_time": format_seconds_to_hhmmss(total_idle_time_seconds),
        "total_browser_time": format_seconds_to_hhmmss(total_browser_time_seconds),
        "total_logged_time": format_seconds_to_hhmmss(total_logged_time_seconds),
        "idle_sessions": idle_sessions_count,
        "last_activity_at": last_activity_at,
        "category_summary": category_summary,
        "website_summary": website_summary
    }


def get_user_unified_timeline(
    db: Session,
    user: User,
    limit: int = 100,
    offset: int = 0,
) -> list[UnifiedTimelineItem]:
    """
    Retrieves a unified chronological timeline of browser activities and idle sessions for the user.
    
    Combines both BrowserActivity and IdleSession records, sorted by start time descending.
    Each item includes a 'type' field to distinguish between 'activity' and 'idle'.
    
    Args:
        db: Database session
        user: Authenticated user
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of unified timeline items
    """
    if user.organization_id is None:
        return []
    
    # Query browser activities
    browser_activities = (
        db.query(BrowserActivity)
        .filter(
            BrowserActivity.organization_id == user.organization_id,
            BrowserActivity.user_id == user.id,
        )
        .all()
    )
    
    # Query idle sessions
    idle_sessions = (
        db.query(IdleSession)
        .filter(
            IdleSession.organization_id == user.organization_id,
            IdleSession.user_id == user.id,
        )
        .all()
    )
    
    # Convert to unified timeline items
    timeline_items = []
    
    for activity in browser_activities:
        timeline_items.append(UnifiedTimelineItem(
            type="activity",
            id=activity.id,
            organization_id=activity.organization_id,
            user_id=activity.user_id,
            start_time=activity.session_start_time,
            end_time=activity.session_end_time,
            duration_seconds=activity.duration_seconds,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
            browser_name=activity.browser_name,
            website_url=activity.website_url,
            website_domain=activity.website_domain,
            page_title=activity.page_title,
            website_category=activity.website_category,
            productivity_classification=activity.productivity_classification,
            username=activity.username,
        ))
    
    for session in idle_sessions:
        timeline_items.append(UnifiedTimelineItem(
            type="idle",
            id=session.id,
            organization_id=session.organization_id,
            user_id=session.user_id,
            start_time=session.idle_start_time,
            end_time=session.idle_end_time,
            duration_seconds=session.duration_seconds,
            created_at=session.created_at,
            updated_at=session.updated_at,
            idle_start_time=session.idle_start_time,
            idle_end_time=session.idle_end_time,
        ))
    
    # Sort by start time descending
    timeline_items.sort(key=lambda x: x.start_time, reverse=True)
    
    # Apply pagination
    return timeline_items[offset:offset + limit]


def get_organization_unified_timeline(
    db: Session,
    user: User,
    limit: int = 100,
    offset: int = 0,
) -> list[UnifiedTimelineItem]:
    """
    Retrieves a unified chronological timeline of browser activities and idle sessions for the organization.
    
    Only accessible by admins. Returns all activities and idle sessions across the organization.
    Each item includes a 'type' field to distinguish between 'activity' and 'idle'.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of unified timeline items for the organization
    """
    if user.organization_id is None:
        return []
    
    # Query browser activities for organization
    browser_activities = (
        db.query(BrowserActivity)
        .filter(BrowserActivity.organization_id == user.organization_id)
        .all()
    )
    
    # Query idle sessions for organization
    idle_sessions = (
        db.query(IdleSession)
        .filter(IdleSession.organization_id == user.organization_id)
        .all()
    )
    
    # Convert to unified timeline items
    timeline_items = []
    
    for activity in browser_activities:
        timeline_items.append(UnifiedTimelineItem(
            type="activity",
            id=activity.id,
            organization_id=activity.organization_id,
            user_id=activity.user_id,
            start_time=activity.session_start_time,
            end_time=activity.session_end_time,
            duration_seconds=activity.duration_seconds,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
            browser_name=activity.browser_name,
            website_url=activity.website_url,
            website_domain=activity.website_domain,
            page_title=activity.page_title,
            website_category=activity.website_category,
            productivity_classification=activity.productivity_classification,
            username=activity.username,
        ))
    
    for session in idle_sessions:
        timeline_items.append(UnifiedTimelineItem(
            type="idle",
            id=session.id,
            organization_id=session.organization_id,
            user_id=session.user_id,
            start_time=session.idle_start_time,
            end_time=session.idle_end_time,
            duration_seconds=session.duration_seconds,
            created_at=session.created_at,
            updated_at=session.updated_at,
            idle_start_time=session.idle_start_time,
            idle_end_time=session.idle_end_time,
        ))
    
    # Sort by start time descending
    timeline_items.sort(key=lambda x: x.start_time, reverse=True)
    
    # Apply pagination
    return timeline_items[offset:offset + limit]

