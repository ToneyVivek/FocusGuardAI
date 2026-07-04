import json
from typing import Optional, Any

from sqlalchemy.orm import Session

import logging
from app.models.models import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """
    Creates an audit log entry for security-relevant events.
    
    IMPORTANT: This function does NOT commit. The caller must handle transaction lifecycle.
    This ensures audit logs participate in the parent transaction and can be rolled back.
    
    Args:
        db: Database session
        action: Action type (e.g., "user_login", "org_created", "invitation_sent")
        user_id: ID of the user performing the action
        organization_id: ID of the organization context
        metadata: Additional context data as a dictionary
        
    Returns:
        Created AuditLog instance (not yet committed)
    """
    metadata_json = json.dumps(metadata) if metadata else None
    
    audit_log = AuditLog(
        action=action,
        user_id=user_id,
        organization_id=organization_id,
        audit_metadata=metadata_json,
    )
    
    db.add(audit_log)
    db.flush()  # Flush to get ID but do NOT commit
    
    logger.info(
        "Audit log created: action=%s, user_id=%s, organization_id=%s",
        action,
        user_id,
        organization_id,
    )
    
    return audit_log
