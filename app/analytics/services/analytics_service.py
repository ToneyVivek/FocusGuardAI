"""
Analytics service for FocusGuard.

Provides analytics methods for individual employees and organizations.
Uses query layer for database operations and utils for calculations.
"""
from datetime import date
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import ProductivityClassification, WebsiteCategory, User
from app.analytics.queries.analytics_queries import (
    get_summary_metrics_query,
    get_productivity_breakdown_query,
    get_category_breakdown_query,
    get_domain_breakdown_query,
    get_timeline_query,
    get_activity_events_count_query,
    get_employee_rankings_query,
    get_trends_query,
)
from app.analytics.utils.focus_score import calculate_focus_score
from app.analytics.schemas.analytics_schemas import (
    SummaryMetrics,
    ProductivityBreakdown,
    ProductivityType,
    CategoryBreakdown,
    CategoryBreakdownItem,
    DomainBreakdown,
    DomainBreakdownItem,
    Timeline,
    TimelineItem,
    FocusScore,
    UserSummaryResponseV2,
    OrganizationSummaryResponseV2,
    EmployeeRankings,
    EmployeeRankingItem,
    Trends,
    TrendDataPoint,
)


def get_user_summary(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> UserSummaryResponseV2:
    """
    Get analytics summary for the authenticated user.
    
    Args:
        db: Database session
        user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        User summary response
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    # Get summary metrics
    browser_totals, idle_totals = get_summary_metrics_query(
        db, user.organization_id, user.id, start_date, end_date
    )
    
    total_focus_time = getattr(browser_totals, "total_focus_time", 0) or 0
    completed_sessions = getattr(browser_totals, "completed_sessions", 0) or 0
    idle_time = getattr(idle_totals, "idle_time", 0) or 0
    idle_sessions = getattr(idle_totals, "idle_sessions", 0) or 0
    
    # Get activity events count
    activity_events = get_activity_events_count_query(
        db, user.organization_id, user.id, start_date, end_date
    )
    
    # Get productivity breakdown
    productivity_data = get_productivity_breakdown_query(
        db, user.organization_id, user.id, start_date, end_date
    )
    
    productive_time = 0
    neutral_time = 0
    non_productive_time = 0
    
    for classification, duration in productivity_data:
        if classification == ProductivityClassification.PRODUCTIVE:
            productive_time = duration or 0
        elif classification == ProductivityClassification.NEUTRAL:
            neutral_time = duration or 0
        elif classification == ProductivityClassification.NON_PRODUCTIVE:
            non_productive_time = duration or 0
    
    total_active_time = productive_time + neutral_time + non_productive_time
    
    # Build summary metrics
    metrics = SummaryMetrics(
        total_focus_time=total_focus_time,
        productive_time=productive_time,
        neutral_time=neutral_time,
        non_productive_time=non_productive_time,
        idle_time=idle_time,
        completed_sessions=completed_sessions,
        idle_sessions=idle_sessions,
        activity_events=activity_events
    )
    
    # Build productivity breakdown
    productivity = ProductivityBreakdown(
        productive=ProductivityType(
            duration_seconds=productive_time,
            percentage=_calculate_percentage(productive_time, total_active_time)
        ),
        neutral=ProductivityType(
            duration_seconds=neutral_time,
            percentage=_calculate_percentage(neutral_time, total_active_time)
        ),
        non_productive=ProductivityType(
            duration_seconds=non_productive_time,
            percentage=_calculate_percentage(non_productive_time, total_active_time)
        )
    )
    
    # Build category breakdown
    category_data = get_category_breakdown_query(
        db, user.organization_id, user.id, start_date, end_date
    )
    
    categories = [
        CategoryBreakdownItem(
            category=_get_category_display_name(category),
            duration_seconds=duration,
            percentage=_calculate_percentage(duration, total_focus_time),
            session_count=session_count
        )
        for category, duration, session_count in category_data
    ]
    
    category_breakdown = CategoryBreakdown(categories=categories)
    
    # Build domain breakdown
    domain_data = get_domain_breakdown_query(
        db, user.organization_id, user.id, start_date, end_date, limit=10
    )
    
    domains = [
        DomainBreakdownItem(
            domain=domain,
            duration_seconds=duration,
            session_count=session_count
        )
        for domain, duration, session_count in domain_data
    ]
    
    domain_breakdown = DomainBreakdown(domains=domains)
    
    # Calculate focus score
    focus_score = FocusScore(
        score=calculate_focus_score(productive_time, total_active_time),
        productive_time=productive_time,
        total_active_time=total_active_time
    )
    
    return UserSummaryResponseV2(
        metrics=metrics,
        productivity=productivity,
        categories=category_breakdown,
        domains=domain_breakdown,
        focus_score=focus_score
    )


def get_user_productivity(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> ProductivityBreakdown:
    """
    Get productivity breakdown for the authenticated user.
    
    Args:
        db: Database session
        user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Productivity breakdown
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    productivity_data = get_productivity_breakdown_query(
        db, user.organization_id, user.id, start_date, end_date
    )
    
    productive_time = 0
    neutral_time = 0
    non_productive_time = 0
    
    for classification, duration in productivity_data:
        if classification == ProductivityClassification.PRODUCTIVE:
            productive_time = duration or 0
        elif classification == ProductivityClassification.NEUTRAL:
            neutral_time = duration or 0
        elif classification == ProductivityClassification.NON_PRODUCTIVE:
            non_productive_time = duration or 0
    
    total_active_time = productive_time + neutral_time + non_productive_time
    
    return ProductivityBreakdown(
        productive=ProductivityType(
            duration_seconds=productive_time,
            percentage=_calculate_percentage(productive_time, total_active_time)
        ),
        neutral=ProductivityType(
            duration_seconds=neutral_time,
            percentage=_calculate_percentage(neutral_time, total_active_time)
        ),
        non_productive=ProductivityType(
            duration_seconds=non_productive_time,
            percentage=_calculate_percentage(non_productive_time, total_active_time)
        )
    )


def get_user_category_breakdown(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> CategoryBreakdown:
    """
    Get category breakdown for the authenticated user.
    
    Args:
        db: Database session
        user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Category breakdown
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    # Get total focus time for percentage calculation
    browser_totals, _ = get_summary_metrics_query(
        db, user.organization_id, user.id, start_date, end_date
    )
    total_focus_time = getattr(browser_totals, "total_focus_time", 0) or 0
    
    category_data = get_category_breakdown_query(
        db, user.organization_id, user.id, start_date, end_date
    )
    
    categories = [
        CategoryBreakdownItem(
            category=_get_category_display_name(category),
            duration_seconds=duration,
            percentage=_calculate_percentage(duration, total_focus_time),
            session_count=session_count
        )
        for category, duration, session_count in category_data
    ]
    
    return CategoryBreakdown(categories=categories)


def get_user_domain_breakdown(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10
) -> DomainBreakdown:
    """
    Get domain breakdown for the authenticated user.
    
    Args:
        db: Database session
        user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of domains to return
        
    Returns:
        Domain breakdown
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    domain_data = get_domain_breakdown_query(
        db, user.organization_id, user.id, start_date, end_date, limit
    )
    
    domains = [
        DomainBreakdownItem(
            domain=domain,
            duration_seconds=duration,
            session_count=session_count
        )
        for domain, duration, session_count in domain_data
    ]
    
    return DomainBreakdown(domains=domains)


def get_user_timeline(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
) -> Timeline:
    """
    Get timeline for the authenticated user.
    
    Args:
        db: Database session
        user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of records to return
        
    Returns:
        Timeline
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    timeline_data = get_timeline_query(
        db, user.organization_id, user.id, start_date, end_date, limit
    )
    
    items = [
        TimelineItem(
            session_id=activity.id,
            start_time=activity.session_start_time,
            end_time=activity.session_end_time,
            duration_seconds=activity.duration_seconds,
            website_url=activity.website_url,
            website_domain=activity.website_domain,
            category=_get_category_display_name(activity.website_category),
            productivity=str(activity.productivity_classification)
        )
        for activity in timeline_data
    ]
    
    return Timeline(items=items)


def get_org_summary(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> OrganizationSummaryResponseV2:
    """
    Get analytics summary for the organization.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Organization summary response
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    # Get summary metrics
    browser_totals, idle_totals = get_summary_metrics_query(
        db, user.organization_id, None, start_date, end_date
    )
    
    total_focus_time = getattr(browser_totals, "total_focus_time", 0) or 0
    completed_sessions = getattr(browser_totals, "completed_sessions", 0) or 0
    idle_time = getattr(idle_totals, "idle_time", 0) or 0
    idle_sessions = getattr(idle_totals, "idle_sessions", 0) or 0
    
    # Get activity events count
    activity_events = get_activity_events_count_query(
        db, user.organization_id, None, start_date, end_date
    )
    
    # Get productivity breakdown
    productivity_data = get_productivity_breakdown_query(
        db, user.organization_id, None, start_date, end_date
    )
    
    productive_time = 0
    neutral_time = 0
    non_productive_time = 0
    
    for classification, duration in productivity_data:
        if classification == ProductivityClassification.PRODUCTIVE:
            productive_time = duration or 0
        elif classification == ProductivityClassification.NEUTRAL:
            neutral_time = duration or 0
        elif classification == ProductivityClassification.NON_PRODUCTIVE:
            non_productive_time = duration or 0
    
    total_active_time = productive_time + neutral_time + non_productive_time
    
    # Build summary metrics
    metrics = SummaryMetrics(
        total_focus_time=total_focus_time,
        productive_time=productive_time,
        neutral_time=neutral_time,
        non_productive_time=non_productive_time,
        idle_time=idle_time,
        completed_sessions=completed_sessions,
        idle_sessions=idle_sessions,
        activity_events=activity_events
    )
    
    # Build productivity breakdown
    productivity = ProductivityBreakdown(
        productive=ProductivityType(
            duration_seconds=productive_time,
            percentage=_calculate_percentage(productive_time, total_active_time)
        ),
        neutral=ProductivityType(
            duration_seconds=neutral_time,
            percentage=_calculate_percentage(neutral_time, total_active_time)
        ),
        non_productive=ProductivityType(
            duration_seconds=non_productive_time,
            percentage=_calculate_percentage(non_productive_time, total_active_time)
        )
    )
    
    # Build category breakdown
    category_data = get_category_breakdown_query(
        db, user.organization_id, None, start_date, end_date
    )
    
    categories = [
        CategoryBreakdownItem(
            category=_get_category_display_name(category),
            duration_seconds=duration,
            percentage=_calculate_percentage(duration, total_focus_time),
            session_count=session_count
        )
        for category, duration, session_count in category_data
    ]
    
    category_breakdown = CategoryBreakdown(categories=categories)
    
    # Build domain breakdown
    domain_data = get_domain_breakdown_query(
        db, user.organization_id, None, start_date, end_date, limit=10
    )
    
    domains = [
        DomainBreakdownItem(
            domain=domain,
            duration_seconds=duration,
            session_count=session_count
        )
        for domain, duration, session_count in domain_data
    ]
    
    domain_breakdown = DomainBreakdown(domains=domains)
    
    # Get employee count
    employee_count = db.query(User).filter(
        User.organization_id == user.organization_id,
        User.is_active == True
    ).count()
    
    return OrganizationSummaryResponseV2(
        metrics=metrics,
        productivity=productivity,
        categories=category_breakdown,
        domains=domain_breakdown,
        employee_count=employee_count
    )


def get_org_productivity(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> ProductivityBreakdown:
    """
    Get productivity breakdown for the organization.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Productivity breakdown
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    productivity_data = get_productivity_breakdown_query(
        db, user.organization_id, None, start_date, end_date
    )
    
    productive_time = 0
    neutral_time = 0
    non_productive_time = 0
    
    for classification, duration in productivity_data:
        if classification == ProductivityClassification.PRODUCTIVE:
            productive_time = duration or 0
        elif classification == ProductivityClassification.NEUTRAL:
            neutral_time = duration or 0
        elif classification == ProductivityClassification.NON_PRODUCTIVE:
            non_productive_time = duration or 0
    
    total_active_time = productive_time + neutral_time + non_productive_time
    
    return ProductivityBreakdown(
        productive=ProductivityType(
            duration_seconds=productive_time,
            percentage=_calculate_percentage(productive_time, total_active_time)
        ),
        neutral=ProductivityType(
            duration_seconds=neutral_time,
            percentage=_calculate_percentage(neutral_time, total_active_time)
        ),
        non_productive=ProductivityType(
            duration_seconds=non_productive_time,
            percentage=_calculate_percentage(non_productive_time, total_active_time)
        )
    )


def get_org_category_breakdown(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> CategoryBreakdown:
    """
    Get category breakdown for the organization.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Category breakdown
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    # Get total focus time for percentage calculation
    browser_totals, _ = get_summary_metrics_query(
        db, user.organization_id, None, start_date, end_date
    )
    total_focus_time = getattr(browser_totals, "total_focus_time", 0) or 0
    
    category_data = get_category_breakdown_query(
        db, user.organization_id, None, start_date, end_date
    )
    
    categories = [
        CategoryBreakdownItem(
            category=_get_category_display_name(category),
            duration_seconds=duration,
            percentage=_calculate_percentage(duration, total_focus_time),
            session_count=session_count
        )
        for category, duration, session_count in category_data
    ]
    
    return CategoryBreakdown(categories=categories)


def get_org_domain_breakdown(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10
) -> DomainBreakdown:
    """
    Get domain breakdown for the organization.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of domains to return
        
    Returns:
        Domain breakdown
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    domain_data = get_domain_breakdown_query(
        db, user.organization_id, None, start_date, end_date, limit
    )
    
    domains = [
        DomainBreakdownItem(
            domain=domain,
            duration_seconds=duration,
            session_count=session_count
        )
        for domain, duration, session_count in domain_data
    ]
    
    return DomainBreakdown(domains=domains)


def get_org_employee_rankings(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10
) -> EmployeeRankings:
    """
    Get employee rankings for the organization.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of employees to return
        
    Returns:
        Employee rankings
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    ranking_data = get_employee_rankings_query(
        db, user.organization_id, start_date, end_date, limit
    )
    
    rankings = [
        EmployeeRankingItem(
            user_id=user_id,
            username=username,
            focus_score=calculate_focus_score(productive_time, total_active_time),
            productive_time=productive_time,
            total_active_time=total_active_time
        )
        for user_id, username, productive_time, total_active_time in ranking_data
    ]
    
    return EmployeeRankings(rankings=rankings)


def get_org_trends(
    db: Session,
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Trends:
    """
    Get trends for the organization.
    
    Args:
        db: Database session
        user: Authenticated user (must be admin)
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Trends data
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view analytics."
        )
    
    trend_data = get_trends_query(
        db, user.organization_id, None, start_date, end_date
    )
    
    data_points = [
        TrendDataPoint(
            date=str(trend_date),
            productive_time=productive_time,
            total_active_time=total_active_time,
            focus_score=calculate_focus_score(productive_time, total_active_time)
        )
        for trend_date, productive_time, total_active_time in trend_data
    ]
    
    return Trends(data_points=data_points)


def _calculate_percentage(value: int, total: int) -> float:
    """Calculate percentage, handling division by zero."""
    if total == 0:
        return 0.0
    return round((value / total) * 100, 2)


def _get_category_display_name(category: WebsiteCategory) -> str:
    """Get display name for website category."""
    display_names = {
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
    return display_names.get(category, str(category).replace("_", " ").title())
