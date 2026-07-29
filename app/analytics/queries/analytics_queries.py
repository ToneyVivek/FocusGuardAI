"""
Analytics query layer for FocusGuard.

Provides reusable query helpers for analytics calculations.
Uses SQL aggregation for performance.
"""
from datetime import datetime, date
from typing import Optional, Tuple, List, Any
from sqlalchemy import func, and_, desc, case
from sqlalchemy.orm import Session

from app.models.analytics import BrowserActivity
from app.models.models import IdleSession, ProductivityClassification, WebsiteCategory


def apply_date_filter(query, model, start_date: Optional[date], end_date: Optional[date], time_field: str):
    """
    Apply date filter to a query.
    
    Args:
        query: SQLAlchemy query object
        model: Model class
        start_date: Optional start date
        end_date: Optional end date
        time_field: Name of the time field to filter on
        
    Returns:
        Filtered query
    """
    conditions = []
    
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        conditions.append(getattr(model, time_field) >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        conditions.append(getattr(model, time_field) <= end_datetime)
    
    if conditions:
        query = query.filter(and_(*conditions))
    
    return query


def get_summary_metrics_query(
    db: Session,
    organization_id: int,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Tuple[Any, Any]:
    """
    Get summary metrics for browser activities and idle sessions.
    
    Args:
        db: Database session
        organization_id: Organization ID
        user_id: Optional user ID for user-specific queries
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Tuple of (browser_totals, idle_totals)
    """
    # Browser activity totals
    browser_query = db.query(
        func.sum(BrowserActivity.duration_seconds).label("total_focus_time"),
        func.count(BrowserActivity.id).label("completed_sessions")
    ).filter(BrowserActivity.organization_id == organization_id)
    
    if user_id:
        browser_query = browser_query.filter(BrowserActivity.user_id == user_id)
    
    browser_query = apply_date_filter(browser_query, BrowserActivity, start_date, end_date, "session_start_time")
    browser_totals = browser_query.first()
    
    # Idle session totals
    idle_query = db.query(
        func.sum(IdleSession.duration_seconds).label("idle_time"),
        func.count(IdleSession.id).label("idle_sessions")
    ).filter(IdleSession.organization_id == organization_id)
    
    if user_id:
        idle_query = idle_query.filter(IdleSession.user_id == user_id)
    
    idle_query = apply_date_filter(idle_query, IdleSession, start_date, end_date, "idle_start_time")
    idle_totals = idle_query.first()
    
    return browser_totals, idle_totals


def get_productivity_breakdown_query(
    db: Session,
    organization_id: int,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Tuple[str, int]]:
    """
    Get productivity breakdown by classification.
    
    Args:
        db: Database session
        organization_id: Organization ID
        user_id: Optional user ID for user-specific queries
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of (classification, duration_seconds) tuples
    """
    query = db.query(
        BrowserActivity.productivity_classification,
        func.sum(BrowserActivity.duration_seconds).label("duration")
    ).filter(BrowserActivity.organization_id == organization_id)
    
    if user_id:
        query = query.filter(BrowserActivity.user_id == user_id)
    
    query = apply_date_filter(query, BrowserActivity, start_date, end_date, "session_start_time")
    query = query.group_by(BrowserActivity.productivity_classification).all()
    
    return query


def get_category_breakdown_query(
    db: Session,
    organization_id: int,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Tuple[str, int, int]]:
    """
    Get category breakdown with duration and session count.
    
    Args:
        db: Database session
        organization_id: Organization ID
        user_id: Optional user ID for user-specific queries
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of (category, duration_seconds, session_count) tuples
    """
    query = db.query(
        BrowserActivity.website_category,
        func.sum(BrowserActivity.duration_seconds).label("duration"),
        func.count(BrowserActivity.id).label("session_count")
    ).filter(BrowserActivity.organization_id == organization_id)
    
    if user_id:
        query = query.filter(BrowserActivity.user_id == user_id)
    
    query = apply_date_filter(query, BrowserActivity, start_date, end_date, "session_start_time")
    query = query.group_by(BrowserActivity.website_category).order_by(desc("duration")).all()
    
    return query


def get_domain_breakdown_query(
    db: Session,
    organization_id: int,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10
) -> List[Tuple[str, int, int]]:
    """
    Get domain breakdown with duration and session count.
    
    Args:
        db: Database session
        organization_id: Organization ID
        user_id: Optional user ID for user-specific queries
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of domains to return
        
    Returns:
        List of (domain, duration_seconds, session_count) tuples
    """
    query = db.query(
        BrowserActivity.website_domain,
        func.sum(BrowserActivity.duration_seconds).label("duration"),
        func.count(BrowserActivity.id).label("session_count")
    ).filter(BrowserActivity.organization_id == organization_id)
    
    if user_id:
        query = query.filter(BrowserActivity.user_id == user_id)
    
    query = apply_date_filter(query, BrowserActivity, start_date, end_date, "session_start_time")
    query = query.group_by(BrowserActivity.website_domain).order_by(desc("duration")).limit(limit).all()
    
    return query


def get_timeline_query(
    db: Session,
    organization_id: int,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
) -> List[BrowserActivity]:
    """
    Get timeline of browser activities.
    
    Args:
        db: Database session
        organization_id: Organization ID
        user_id: Optional user ID for user-specific queries
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of records to return
        
    Returns:
        List of BrowserActivity objects
    """
    query = db.query(BrowserActivity).filter(BrowserActivity.organization_id == organization_id)
    
    if user_id:
        query = query.filter(BrowserActivity.user_id == user_id)
    
    query = apply_date_filter(query, BrowserActivity, start_date, end_date, "session_start_time")
    query = query.order_by(BrowserActivity.session_start_time.desc()).limit(limit).all()
    
    return query


def get_activity_events_count_query(
    db: Session,
    organization_id: int,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    """
    Get count of activity events.
    
    Args:
        db: Database session
        organization_id: Organization ID
        user_id: Optional user ID for user-specific queries
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Count of activity events
    """
    from app.models.analytics import ActivityEvent
    
    query = db.query(func.count(ActivityEvent.id)).filter(ActivityEvent.organization_id == organization_id)
    
    if user_id:
        query = query.filter(ActivityEvent.user_id == user_id)
    
    query = apply_date_filter(query, ActivityEvent, start_date, end_date, "timestamp")
    
    return query.scalar() or 0


def get_employee_rankings_query(
    db: Session,
    organization_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10
) -> List[Tuple[int, str, int, int]]:
    """
    Get employee rankings by focus score.
    
    Args:
        db: Database session
        organization_id: Organization ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of employees to return
        
    Returns:
        List of (user_id, username, productive_time, total_active_time) tuples
    """
    from app.models.models import User
    
    # Calculate productive and total active time per user
    productive_time = func.sum(
        case(
            (BrowserActivity.productivity_classification == ProductivityClassification.PRODUCTIVE, BrowserActivity.duration_seconds),
            else_=0
        )
    )
    
    total_active_time = func.sum(BrowserActivity.duration_seconds)
    
    query = db.query(
        User.id,
        User.full_name,
        productive_time.label("productive_time"),
        total_active_time.label("total_active_time")
    ).join(BrowserActivity, User.id == BrowserActivity.user_id).filter(
        BrowserActivity.organization_id == organization_id
    )
    
    query = apply_date_filter(query, BrowserActivity, start_date, end_date, "session_start_time")
    query = query.group_by(User.id, User.full_name).order_by(desc("productive_time")).limit(limit).all()
    
    return query


def get_trends_query(
    db: Session,
    organization_id: int,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Tuple[date, int, int]]:
    """
    Get trends data grouped by date.
    
    Args:
        db: Database session
        organization_id: Organization ID
        user_id: Optional user ID for user-specific queries
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of (date, productive_time, total_active_time) tuples
    """
    productive_time = func.sum(
        case(
            (BrowserActivity.productivity_classification == ProductivityClassification.PRODUCTIVE, BrowserActivity.duration_seconds),
            else_=0
        )
    )
    
    total_active_time = func.sum(BrowserActivity.duration_seconds)
    
    query = db.query(
        func.date(BrowserActivity.session_start_time).label("date"),
        productive_time.label("productive_time"),
        total_active_time.label("total_active_time")
    ).filter(BrowserActivity.organization_id == organization_id)
    
    if user_id:
        query = query.filter(BrowserActivity.user_id == user_id)
    
    query = apply_date_filter(query, BrowserActivity, start_date, end_date, "session_start_time")
    query = query.group_by(func.date(BrowserActivity.session_start_time)).order_by("date").all()
    
    return query
