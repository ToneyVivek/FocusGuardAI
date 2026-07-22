from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies.deps import get_current_admin, get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.models.models import User
from app.schemas.analytics_schemas import (
    BrowserActivityCreate,
    BrowserActivityBatchCreate,
    BrowserActivityResponse,
    AnalyticsSummaryResponse,
    UnifiedTimelineItem,
)
from app.schemas.idle_schemas import IdleSessionCreate, IdleSessionBatchCreate, IdleSessionResponse
from app.schemas.activity_schemas import ActivityEventCreate, ActivityEventBatchCreate, ActivityEventBatchResponse
from app.services.analytics_service import (
    get_organization_activities,
    get_user_activities,
    record_browser_activity,
    get_user_analytics_summary,
    get_user_unified_timeline,
    get_organization_unified_timeline,
    parse_and_validate_date_filter,
)
from app.services.idle_session_service import create_idle_session, get_user_idle_sessions
from app.services.activity_service import create_activity_events_batch

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


@router.post(
    "/activity/batch",
    response_model=list[BrowserActivityResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
def record_activity_batch(
    request: Request,
    batch_in: BrowserActivityBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Records multiple completed browser sessions in a batch.
    
    Called by browser extension for batch synchronization.
    Allows uploading up to 50 sessions in a single request.
    
    Browser extension provides raw browser data for each session:
    - browser_name, website_url, website_domain, page_title
    - session_start_time, session_end_time
    
    Backend determines for each session:
    - website_category (via classification service)
    - productivity_classification (via classification service)
    - duration_seconds (calculated from timestamps)
    - organization_id (from JWT, not client)
    - user_id (from JWT, not client)
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically extracted from authenticated user
    Rate Limiting: 20 requests per minute per IP
    """
    results = []
    for activity_in in batch_in.sessions:
        result = record_browser_activity(db=db, activity_in=activity_in, user=current_user)
        results.append(result)
    return results


@router.get("/activity/my", response_model=list[UnifiedTimelineItem])
@limiter.limit("60/minute")
def get_my_activities(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500, description="Number of records to return (max 500)"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    start_date: Optional[str] = Query(default=None, description="Filter activities from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter activities until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the authenticated user's unified timeline of browser activities and idle sessions.
    
    Returns both browser activities and idle sessions from the user's organization only,
    sorted by start time descending. Each item includes a 'type' field to distinguish
    between 'activity' and 'idle'.
    
    Supports optional date filtering via start_date and end_date parameters.
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    # Validate date filters
    parsed_start, parsed_end = parse_and_validate_date_filter(start_date, end_date)
    
    return get_user_unified_timeline(
        db=db, 
        user=current_user, 
        limit=limit, 
        offset=offset,
        start_date=parsed_start,
        end_date=parsed_end
    )


@router.get("/activity/organization", response_model=list[UnifiedTimelineItem])
@limiter.limit("60/minute")
def get_organization_activity(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500, description="Number of records to return (max 500)"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    start_date: Optional[str] = Query(default=None, description="Filter activities from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter activities until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Retrieves all browser activities and idle sessions for the admin's organization.
    
    Only accessible by organization admins.
    Returns both browser activities and idle sessions across all users in the organization,
    sorted by start time descending. Each item includes a 'type' field to distinguish
    between 'activity' and 'idle'.
    
    Supports optional date filtering via start_date and end_date parameters.
    
    Authentication: JWT token required (Bearer token)
    Authorization: ADMIN role required
    Organization: Automatically filtered by admin's organization
    Rate Limiting: 60 requests per minute per IP
    """
    # Validate date filters
    parsed_start, parsed_end = parse_and_validate_date_filter(start_date, end_date)
    
    return get_organization_unified_timeline(
        db=db, 
        user=current_admin, 
        limit=limit, 
        offset=offset,
        start_date=parsed_start,
        end_date=parsed_end
    )


@router.get("/summary/my", response_model=AnalyticsSummaryResponse)
@limiter.limit("60/minute")
def get_my_analytics_summary(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter summary from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter summary until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Computes and retrieves the authenticated user's aggregated productivity and activity summary.

    Returns productivity totals, idle time statistics, `last_activity_at`, and ordered breakdowns
    for categories and websites. Each category/website entry includes `time_spent` (HH:MM:SS),
    `duration_seconds`, and `percentage` (share of total tracked time). Zero-duration entries are excluded.

    Now includes:
    - idle_time: Total idle time in HH:MM:SS
    - total_browser_time: Total browser activity time in HH:MM:SS
    - total_logged_time: Combined browser + idle time in HH:MM:SS
    - idle_sessions: Count of idle sessions recorded

    Supports optional date filtering via start_date and end_date parameters.

    Authentication: JWT token required (Bearer token)
    Organization: Automatically derived from the current authenticated user's profile.
    Rate Limiting: 60 requests per minute per IP.
    """
    # Validate date filters
    parsed_start, parsed_end = parse_and_validate_date_filter(start_date, end_date)
    
    return get_user_analytics_summary(
        db=db, 
        user=current_user,
        start_date=parsed_start,
        end_date=parsed_end
    )


@router.post(
    "/idle",
    response_model=IdleSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("100/minute")
def record_idle_session(
    request: Request,
    idle_in: IdleSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Records an idle session for the authenticated user.

    Browser extension sends idle session data when user was inactive.
    Backend validates timestamps, calculates duration, and enforces idle threshold.

    Browser extension provides:
    - idle_start_time: When the idle period began
    - idle_end_time: When the idle period ended

    Backend determines:
    - duration_seconds (calculated from timestamps)
    - organization_id (from JWT, not client)
    - user_id (from JWT, not client)
    - Validates duration >= IDLE_THRESHOLD_SECONDS (default 300s / 5 minutes)

    Authentication: JWT token required (Bearer token)
    Organization: Automatically extracted from authenticated user
    Rate Limiting: 100 requests per minute per IP
    """
    return create_idle_session(db=db, idle_in=idle_in, user=current_user)


@router.post(
    "/idle/batch",
    response_model=list[IdleSessionResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
def record_idle_session_batch(
    request: Request,
    batch_in: IdleSessionBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Records multiple idle sessions in a batch.

    Called by browser extension for batch synchronization.
    Allows uploading up to 50 idle sessions in a single request.

    Browser extension provides raw idle data for each session:
    - idle_start_time: When the idle period began
    - idle_end_time: When the idle period ended

    Backend determines for each session:
    - duration_seconds (calculated from timestamps)
    - organization_id (from JWT, not client)
    - user_id (from JWT, not client)

    Authentication: JWT token required (Bearer token)
    Organization: Automatically extracted from authenticated user
    Rate Limiting: 20 requests per minute per IP
    """
    results = []
    for idle_in in batch_in.sessions:
        result = create_idle_session(db=db, idle_in=idle_in, user=current_user)
        results.append(result)
    return results


@router.post(
    "/events/batch",
    response_model=ActivityEventBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
def record_activity_event_batch(
    request: Request,
    batch_in: ActivityEventBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Records multiple activity events in a batch.

    Called by browser extension for batch synchronization.
    Allows uploading up to 50 activity events in a single request.

    Browser extension provides raw event data for each event:
    - event_id: Unique UUID for idempotency
    - event_type: Type of event (TAB_CREATED, TAB_ACTIVATED, etc.)
    - browser_name: Browser name
    - tab_id, window_id: Context information
    - website_url, website_domain, page_title: Website context
    - previous_url, previous_domain: Navigation context
    - timestamp: Event timestamp
    - metadata: Additional event data (JSON)

    Backend determines for each event:
    - organization_id (from JWT, not client)
    - user_id (from JWT, not client)

    The batch is processed inside a single database transaction.
    Duplicate event_ids are ignored gracefully.
    Partial success is supported - only failed events are retried.

    Response includes statistics:
    - inserted: Number of events successfully inserted
    - duplicates: Number of duplicate event_ids ignored
    - failed: Number of events that failed to insert

    Authentication: JWT token required (Bearer token)
    Organization: Automatically extracted from authenticated user
    Rate Limiting: 20 requests per minute per IP
    """
    result = create_activity_events_batch(db=db, batch_in=batch_in, user=current_user)
    return result


@router.get("/idle/my", response_model=list[IdleSessionResponse])
@limiter.limit("60/minute")
def get_my_idle_sessions(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500, description="Number of records to return (max 500)"),
    start_date: Optional[str] = Query(default=None, description="Filter idle sessions from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter idle sessions until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the authenticated user's idle sessions.

    Returns idle sessions from the user's organization only, ordered by start time descending.
    
    Supports optional date filtering via start_date and end_date parameters.

    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    # Validate date filters
    parsed_start, parsed_end = parse_and_validate_date_filter(start_date, end_date)
    
    return get_user_idle_sessions(
        db=db, 
        user=current_user, 
        limit=limit,
        start_date=parsed_start,
        end_date=parsed_end
    )

