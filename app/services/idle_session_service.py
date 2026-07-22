"""
Idle session service for tracking user inactivity periods.

Features:
- Validates idle session timestamps
- Calculates duration from timestamps
- Enforces minimum idle threshold
- Multi-tenant isolation
- Audit logging
- Transaction-safe operations
- Date range filtering
"""
import logging
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.config.config import settings
from app.models.models import IdleSession, User
from app.schemas.idle_schemas import IdleSessionCreate, IdleSessionResponse
from app.services.audit import create_audit_log

logger = logging.getLogger(__name__)


def calculate_duration_seconds(start_time: datetime, end_time: datetime) -> int:
    """
    Calculate duration in seconds between two timestamps.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp
        
    Returns:
        Duration in seconds (rounded)
    """
    duration = (end_time - start_time).total_seconds()
    return int(round(duration))


def validate_idle_session(
    idle_start_time: datetime,
    idle_end_time: datetime,
    user: User,
) -> None:
    """
    Validate idle session data.
    
    Args:
        idle_start_time: When idle period started
        idle_end_time: When idle period ended
        user: Authenticated user
        
    Raises:
        HTTPException: If validation fails
    """
    # Ensure timestamps are timezone-aware
    if idle_start_time.tzinfo is None:
        idle_start_time = idle_start_time.replace(tzinfo=timezone.utc)
    if idle_end_time.tzinfo is None:
        idle_end_time = idle_end_time.replace(tzinfo=timezone.utc)
    
    # Validate timing
    if idle_end_time <= idle_start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="idle_end_time must be after idle_start_time",
        )
    
    # Calculate duration
    duration_seconds = calculate_duration_seconds(idle_start_time, idle_end_time)
    
    # Validate duration is positive
    if duration_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be greater than 0 seconds",
        )
    
    # Validate against idle threshold
    if duration_seconds < settings.IDLE_MIN_DURATION_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Idle session duration ({duration_seconds}s) is below threshold ({settings.IDLE_MIN_DURATION_SECONDS}s)",
        )
    
    # Validate user has organization
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to record idle sessions",
        )


def create_idle_session(
    db: Session,
    idle_in: IdleSessionCreate,
    user: User,
) -> IdleSessionResponse:
    """
    Create a new idle session record.
    
    Args:
        db: Database session
        idle_in: Idle session data from request
        user: Authenticated user
        
    Returns:
        Created idle session response
        
    Raises:
        HTTPException: If validation or overlap check fails
    """
    # Validate the idle session
    validate_idle_session(idle_in.idle_start_time, idle_in.idle_end_time, user)
    
    # Ensure timestamps are timezone-aware
    start_time = idle_in.idle_start_time
    end_time = idle_in.idle_end_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    # Calculate duration
    duration_seconds = calculate_duration_seconds(start_time, end_time)
    
    # Check for overlapping idle sessions
    overlapping = (
        db.query(IdleSession)
        .filter(
            IdleSession.user_id == user.id,
            IdleSession.organization_id == user.organization_id,
            IdleSession.idle_start_time < end_time,
            IdleSession.idle_end_time > start_time,
        )
        .first()
    )
    if overlapping is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idle session overlaps an existing idle session.",
        )
    
    # Create database record
    db_idle = IdleSession(
        organization_id=user.organization_id,
        user_id=user.id,
        idle_start_time=start_time,
        idle_end_time=end_time,
        duration_seconds=duration_seconds,
    )
    
    db.add(db_idle)
    db.commit()
    db.refresh(db_idle)
    
    logger.info(
        f"Created idle session for user {user.id}: "
        f"duration={duration_seconds}s, start={start_time}, end={end_time}"
    )
    
    # Audit log
    try:
        create_audit_log(
            db=db,
            action="idle_session_created",
            user_id=user.id,
            organization_id=user.organization_id,
            metadata={
                "idle_session_id": db_idle.id,
                "duration_seconds": duration_seconds,
                "idle_start_time": start_time.isoformat(),
                "idle_end_time": end_time.isoformat(),
            },
        )
        db.commit()
    except Exception as audit_error:
        logger.error(f"Failed to create audit log for idle session: {audit_error}")
        # Don't fail the operation if audit logging fails
    
    return IdleSessionResponse.model_validate(db_idle)


def get_user_idle_sessions(
    db: Session,
    user: User,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[IdleSessionResponse]:
    """
    Get idle sessions for a specific user.
    
    Args:
        db: Database session
        user: Authenticated user
        limit: Maximum number of records to return
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of idle session responses
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to view idle sessions",
        )
    
    query = (
        db.query(IdleSession)
        .filter(
            IdleSession.user_id == user.id,
            IdleSession.organization_id == user.organization_id,
        )
    )
    
    # Apply date filter
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=timezone.utc)
        query = query.filter(IdleSession.idle_start_time >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        if end_datetime.tzinfo is None:
            end_datetime = end_datetime.replace(tzinfo=timezone.utc)
        query = query.filter(IdleSession.idle_start_time <= end_datetime)
    
    idle_sessions = (
        query
        .order_by(IdleSession.idle_start_time.desc())
        .limit(limit)
        .all()
    )
    
    return [IdleSessionResponse.model_validate(session) for session in idle_sessions]
