"""
Analytics router for FocusGuard.

Provides REST endpoints for user and organization analytics.
Separates analytics from telemetry ingestion.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_admin, get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.models.models import User
from app.analytics.services.analytics_service import (
    get_user_summary,
    get_user_productivity,
    get_user_category_breakdown,
    get_user_domain_breakdown,
    get_user_timeline,
    get_org_summary,
    get_org_productivity,
    get_org_category_breakdown,
    get_org_domain_breakdown,
    get_org_employee_rankings,
    get_org_trends,
)
from app.analytics.schemas.analytics_schemas import (
    UserSummaryResponse,
    ProductivityBreakdown,
    CategoryBreakdown,
    DomainBreakdown,
    Timeline,
    OrganizationSummaryResponse,
    EmployeeRankings,
    Trends,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# User Analytics Endpoints


@router.get("/me/summary", response_model=UserSummaryResponse)
@limiter.limit("60/minute")
def get_me_summary(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get analytics summary for the authenticated user.
    
    Returns summary metrics, productivity breakdown, category breakdown,
    domain breakdown, and focus score.
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_user_summary(db, current_user, parsed_start, parsed_end)


@router.get("/me/productivity", response_model=ProductivityBreakdown)
@limiter.limit("60/minute")
def get_me_productivity(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get productivity breakdown for the authenticated user.
    
    Returns productive, neutral, and non-productive time with percentages.
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_user_productivity(db, current_user, parsed_start, parsed_end)


@router.get("/me/categories", response_model=CategoryBreakdown)
@limiter.limit("60/minute")
def get_me_categories(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get category breakdown for the authenticated user.
    
    Returns website categories with duration, percentage, and session count.
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_user_category_breakdown(db, current_user, parsed_start, parsed_end)


@router.get("/me/domains", response_model=DomainBreakdown)
@limiter.limit("60/minute")
def get_me_domains(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of domains to return"),
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get domain breakdown for the authenticated user.
    
    Returns most used domains with duration and session count.
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_user_domain_breakdown(db, current_user, parsed_start, parsed_end, limit)


@router.get("/me/timeline", response_model=Timeline)
@limiter.limit("60/minute")
def get_me_timeline(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of records to return"),
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get timeline for the authenticated user.
    
    Returns chronological browser activity sessions suitable for charts.
    
    Authentication: JWT token required (Bearer token)
    Organization: Automatically filtered by user's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_user_timeline(db, current_user, parsed_start, parsed_end, limit)


# Organization Analytics Endpoints


@router.get("/org/summary", response_model=OrganizationSummaryResponse)
@limiter.limit("60/minute")
def get_org_summary_endpoint(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get analytics summary for the organization.
    
    Returns summary metrics, productivity breakdown, category breakdown,
    domain breakdown, and employee count.
    
    Authentication: JWT token required (Bearer token)
    Authorization: ADMIN role required
    Organization: Automatically filtered by admin's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_org_summary(db, current_admin, parsed_start, parsed_end)


@router.get("/org/productivity", response_model=ProductivityBreakdown)
@limiter.limit("60/minute")
def get_org_productivity_endpoint(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get productivity breakdown for the organization.
    
    Returns productive, neutral, and non-productive time with percentages.
    
    Authentication: JWT token required (Bearer token)
    Authorization: ADMIN role required
    Organization: Automatically filtered by admin's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_org_productivity(db, current_admin, parsed_start, parsed_end)


@router.get("/org/categories", response_model=CategoryBreakdown)
@limiter.limit("60/minute")
def get_org_categories_endpoint(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get category breakdown for the organization.
    
    Returns website categories with duration, percentage, and session count.
    
    Authentication: JWT token required (Bearer token)
    Authorization: ADMIN role required
    Organization: Automatically filtered by admin's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_org_category_breakdown(db, current_admin, parsed_start, parsed_end)


@router.get("/org/domains", response_model=DomainBreakdown)
@limiter.limit("60/minute")
def get_org_domains_endpoint(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of domains to return"),
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get domain breakdown for the organization.
    
    Returns most used domains with duration and session count.
    
    Authentication: JWT token required (Bearer token)
    Authorization: ADMIN role required
    Organization: Automatically filtered by admin's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_org_domain_breakdown(db, current_admin, parsed_start, parsed_end, limit)


@router.get("/org/employees", response_model=EmployeeRankings)
@limiter.limit("60/minute")
def get_org_employees_endpoint(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of employees to return"),
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get employee rankings for the organization.
    
    Returns employees ranked by focus score.
    
    Authentication: JWT token required (Bearer token)
    Authorization: ADMIN role required
    Organization: Automatically filtered by admin's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_org_employee_rankings(db, current_admin, parsed_start, parsed_end, limit)


@router.get("/org/trends", response_model=Trends)
@limiter.limit("60/minute")
def get_org_trends_endpoint(
    request: Request,
    start_date: Optional[str] = Query(default=None, description="Filter from this date (ISO-8601 format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter until this date (ISO-8601 format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get trends for the organization.
    
    Returns trend data points grouped by date with focus scores.
    
    Authentication: JWT token required (Bearer token)
    Authorization: ADMIN role required
    Organization: Automatically filtered by admin's organization
    Rate Limiting: 60 requests per minute per IP
    """
    parsed_start, parsed_end = _parse_date_filter(start_date, end_date)
    return get_org_trends(db, current_admin, parsed_start, parsed_end)


def _parse_date_filter(start_date: Optional[str], end_date: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    """
    Parse and validate date filter parameters.
    
    Args:
        start_date: ISO-8601 date string (e.g., "2026-07-01")
        end_date: ISO-8601 date string (e.g., "2026-07-15")
        
    Returns:
        Tuple of (start_date, end_date) as date objects or None
        
    Raises:
        HTTPException: If dates are invalid or end_date < start_date
    """
    parsed_start = None
    parsed_end = None
    
    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid start_date format: {start_date}. Expected ISO-8601 format (YYYY-MM-DD)."
            )
    
    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid end_date format: {end_date}. Expected ISO-8601 format (YYYY-MM-DD)."
            )
    
    # Validate date range
    if parsed_start and parsed_end and parsed_end < parsed_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be greater than or equal to start_date"
        )
    
    return parsed_start, parsed_end
