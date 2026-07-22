"""
Activity event service for tracking browser activity events.

Features:
- Batch insertion of activity events
- Duplicate detection by event_id
- Multi-tenant isolation
- Transaction-safe operations
- Audit logging
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.config.config import settings
from app.models.analytics import ActivityEvent
from app.models.models import User
from app.schemas.activity_schemas import ActivityEventCreate, ActivityEventBatchResponse
from app.services.audit import create_audit_log

logger = logging.getLogger(__name__)


def create_activity_event(
    db: Session,
    event_in: ActivityEventCreate,
    user: User,
) -> Optional[ActivityEvent]:
    """
    Create a single activity event record.
    
    Args:
        db: Database session
        event_in: Activity event data from request
        user: Authenticated user
        
    Returns:
        Created activity event, or None if duplicate
    """
    # Check for duplicate event_id
    existing = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.event_id == event_in.event_id)
        .first()
    )
    
    if existing:
        logger.info(f"Duplicate activity event ignored: {event_in.event_id}")
        return None
    
    # Ensure timestamp is timezone-aware
    timestamp = event_in.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    # Create activity event
    activity_event = ActivityEvent(
        organization_id=user.organization_id,
        user_id=user.id,
        event_id=event_in.event_id,
        event_type=event_in.event_type,
        browser_name=event_in.browser_name,
        tab_id=event_in.tab_id,
        window_id=event_in.window_id,
        website_url=event_in.website_url,
        website_domain=event_in.website_domain,
        page_title=event_in.page_title,
        previous_url=event_in.previous_url,
        previous_domain=event_in.previous_domain,
        timestamp=timestamp,
        event_metadata=event_in.event_metadata,
    )
    
    db.add(activity_event)
    db.commit()
    db.refresh(activity_event)
    
    logger.info(f"Activity event created: {activity_event.event_id}, Type: {activity_event.event_type}")
    return activity_event


def create_activity_events_batch(
    db: Session,
    batch_in: ActivityEventBatchCreate,
    user: User,
) -> ActivityEventBatchResponse:
    """
    Create multiple activity events in a single transaction.
    
    Args:
        db: Database session
        batch_in: Batch of activity events from request
        user: Authenticated user
        
    Returns:
        Batch response with statistics (inserted, duplicates, failed)
    """
    inserted_count = 0
    duplicate_count = 0
    failed_count = 0
    
    # Get existing event_ids for duplicate detection
    event_ids = [event.event_id for event in batch_in.events]
    existing_events = (
        db.query(ActivityEvent.event_id)
        .filter(ActivityEvent.event_id.in_(event_ids))
        .all()
    )
    existing_event_ids = {event.event_id for event in existing_events}
    
    try:
        # Process each event
        for event_in in batch_in.events:
            try:
                # Skip duplicates
                if event_in.event_id in existing_event_ids:
                    duplicate_count += 1
                    logger.debug(f"Duplicate activity event skipped: {event_in.event_id}")
                    continue
                
                # Ensure timestamp is timezone-aware
                timestamp = event_in.timestamp
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                
                # Create activity event
                activity_event = ActivityEvent(
                    organization_id=user.organization_id,
                    user_id=user.id,
                    event_id=event_in.event_id,
                    event_type=event_in.event_type,
                    browser_name=event_in.browser_name,
                    tab_id=event_in.tab_id,
                    window_id=event_in.window_id,
                    website_url=event_in.website_url,
                    website_domain=event_in.website_domain,
                    page_title=event_in.page_title,
                    previous_url=event_in.previous_url,
                    previous_domain=event_in.previous_domain,
                    timestamp=timestamp,
                    event_metadata=event_in.event_metadata,
                )
                
                db.add(activity_event)
                inserted_count += 1
                logger.debug(f"Activity event added to batch: {activity_event.event_id}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process activity event {event_in.event_id}: {e}")
                # Continue processing other events
        
        # Commit all successful inserts in one transaction
        db.commit()
        logger.info(
            f"Activity events batch processed - Inserted: {inserted_count}, Duplicates: {duplicate_count}, Failed: {failed_count}"
        )
        
        return ActivityEventBatchResponse(
            inserted=inserted_count,
            duplicates=duplicate_count,
            failed=failed_count,
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Activity events batch transaction failed: {e}")
        raise


def get_user_activity_events(
    db: Session,
    user_id: int,
    organization_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[ActivityEvent]:
    """
    Get activity events for a user with optional filtering.
    
    Args:
        db: Database session
        user_id: User ID
        organization_id: Organization ID
        start_time: Optional start time filter
        end_time: Optional end time filter
        event_type: Optional event type filter
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of activity events
    """
    query = (
        db.query(ActivityEvent)
        .filter(
            ActivityEvent.user_id == user_id,
            ActivityEvent.organization_id == organization_id,
        )
    )
    
    if start_time:
        query = query.filter(ActivityEvent.timestamp >= start_time)
    
    if end_time:
        query = query.filter(ActivityEvent.timestamp <= end_time)
    
    if event_type:
        query = query.filter(ActivityEvent.event_type == event_type)
    
    query = query.order_by(ActivityEvent.timestamp.desc())
    query = query.limit(limit).offset(offset)
    
    return query.all()
