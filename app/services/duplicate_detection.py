"""
Duplicate detection service for browser activity records.

This service isolates duplicate detection logic to support future evolution
from current strategy (user_id + domain + timestamps) to browser-generated
activity UUIDs.

Current Strategy (Version 1):
- Uses (user_id, website_domain, session_start_time, session_end_time)
- Enforced by database unique constraint
- Handles network retries and duplicate submissions

Future Strategy (Version 2):
- Will use browser-generated activity_uuid
- More reliable for complex retry scenarios
- Better support for offline-to-online sync

Migration Path:
1. Add activity_uuid column (nullable initially)
2. Update browser extension to generate UUIDs
3. Update duplicate detection to prefer UUID
4. Make UUID non-nullable after migration
5. Deprecate old strategy

This service provides a clean abstraction layer for this transition.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.analytics import BrowserActivity

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """
    Service for detecting and handling duplicate browser activity records.
    
    Isolates duplicate detection logic to support future migration to
    browser-generated activity UUIDs without scattering logic throughout
    the codebase.
    """
    
    @classmethod
    def check_duplicate(
        cls,
        db: Session,
        user_id: int,
        website_domain: str,
        session_start_time,
        session_end_time,
        activity_uuid: Optional[str] = None,
    ) -> Optional[BrowserActivity]:
        """
        Check if a duplicate browser activity record exists.
        
        Current Strategy (Version 1):
        - Checks for existing record with same (user_id, domain, timestamps)
        
        Future Strategy (Version 2):
        - Will check for existing record with same activity_uuid
        - Fall back to current strategy for backward compatibility
        
        Args:
            db: Database session
            user_id: User ID from JWT
            website_domain: Normalized website domain
            session_start_time: Session start timestamp
            session_end_time: Session end timestamp
            activity_uuid: Optional browser-generated UUID (future)
            
        Returns:
            Existing BrowserActivity if duplicate found, None otherwise
        """
        # Future: When browser extension sends UUIDs, check by UUID first
        # if activity_uuid:
        #     existing = db.query(BrowserActivity).filter(
        #         BrowserActivity.activity_uuid == activity_uuid
        #     ).first()
        #     if existing:
        #         logger.info(f"Duplicate detected by UUID: {activity_uuid}")
        #         return existing
        
        # Current Strategy: Check by user_id + domain + timestamps
        existing = (
            db.query(BrowserActivity)
            .filter(
                BrowserActivity.user_id == user_id,
                BrowserActivity.website_domain == website_domain,
                BrowserActivity.session_start_time == session_start_time,
                BrowserActivity.session_end_time == session_end_time,
            )
            .first()
        )
        
        if existing:
            logger.info(
                f"Duplicate detected by current strategy: user_id={user_id}, "
                f"domain={website_domain}, start={session_start_time}, end={session_end_time}"
            )
        
        return existing
    
    @classmethod
    def is_duplicate_error(cls, error: Exception) -> bool:
        """
        Determine if a database error is a duplicate key violation.
        
        Used to handle idempotent operations - if duplicate detected,
        return existing record instead of failing.
        
        Args:
            error: Database exception
            
        Returns:
            True if error is a duplicate key violation, False otherwise
        """
        error_str = str(error).lower()
        return (
            "duplicate key" in error_str
            or "unique constraint" in error_str
            or "unique_violation" in error_str
        )
    
    @classmethod
    def get_duplicate_key_fields(cls) -> list[str]:
        """
        Return the current duplicate detection key fields.
        
        This method documents the current strategy for future reference
        and makes it easy to see what will change during UUID migration.
        
        Returns:
            List of field names used for duplicate detection
        """
        # Current Strategy (Version 1)
        return ["user_id", "website_domain", "session_start_time", "session_end_time"]
        
        # Future Strategy (Version 2)
        # return ["activity_uuid"]


# Singleton instance for consistency
duplicate_detection_service = DuplicateDetectionService()
