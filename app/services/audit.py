import json
from typing import Optional, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.models import AuditLog

logger = get_logger(__name__)


def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """
    Creates an audit log entry for security-relevant events.
    
    Args:
        db: Database session
        action: Action type (e.g., "user_login", "org_created", "invitation_sent")
        user_id: ID of the user performing the action
        organization_id: ID of the organization context
        metadata: Additional context data as a dictionary
        
    Returns:
        Created AuditLog instance
    """
    metadata_json = json.dumps(metadata) if metadata else None
    
    audit_log = AuditLog(
        action=action,
        user_id=user_id,
        organization_id=organization_id,
        audit_metadata=metadata_json,
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    logger.info(
        "Audit log created: action=%s, user_id=%s, organization_id=%s",
        action,
        user_id,
        organization_id,
    )
    
    return audit_log
