"""
Refresh token service for secure JWT access token renewal.

Security Features:
- SHA-256 hashing of refresh tokens (never store raw tokens)
- Token rotation on each refresh (old token invalidated)
- Configurable expiration (default 7 days)
- Token revocation support
- Transaction-safe operations
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.config import settings
from app.models.models import RefreshToken, User
from app.services.audit import create_audit_log

logger = logging.getLogger(__name__)


# Default refresh token expiration: 7 days
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7


class RefreshTokenService:
    """
    Service for managing refresh tokens with secure hashing and rotation.
    """
    
    @staticmethod
    def _hash_token(token: str) -> bytes:
        """
        Generate SHA-256 hash of a refresh token.
        
        Args:
            token: Raw refresh token string
            
        Returns:
            SHA-256 hash as bytes (32 bytes)
        """
        return hashlib.sha256(token.encode()).digest()
    
    @staticmethod
    def _generate_token() -> str:
        """
        Generate a cryptographically secure random refresh token.
        
        Returns:
            URL-safe random token string
        """
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def _get_expiration(days: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS) -> datetime:
        """
        Calculate expiration timestamp for a refresh token.
        
        Args:
            days: Number of days until expiration
            
        Returns:
            UTC datetime when token expires
        """
        return datetime.now(timezone.utc) + timedelta(days=days)
    
    @staticmethod
    def create_refresh_token(
        db: Session,
        user: User,
        days: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS,
    ) -> str:
        """
        Create a new refresh token for a user.
        
        Stores only the SHA-256 hash of the token, never the raw token.
        
        Args:
            db: Database session
            user: User to create token for
            days: Days until expiration (default 7)
            
        Returns:
            Raw refresh token string (to be sent to client)
        """
        # Generate secure random token
        raw_token = RefreshTokenService._generate_token()
        token_hash = RefreshTokenService._hash_token(raw_token)
        expires_at = RefreshTokenService._get_expiration(days)
        
        # Create database record with hash only
        db_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        
        logger.info(f"Created refresh token for user {user.id}, expires at {expires_at}")
        
        # Audit log
        try:
            create_audit_log(
                db=db,
                action="refresh_token_created",
                user_id=user.id,
                organization_id=user.organization_id,
                metadata={"token_id": db_token.id, "expires_at": expires_at.isoformat()},
            )
            db.commit()
        except Exception as audit_error:
            logger.error(f"Failed to create audit log for refresh token creation: {audit_error}")
            # Don't fail the operation if audit logging fails
        
        return raw_token
    
    @staticmethod
    def verify_refresh_token(db: Session, raw_token: str) -> RefreshToken:
        """
        Verify a refresh token and return the database record.
        
        Args:
            db: Database session
            raw_token: Raw refresh token string from client
            
        Returns:
            RefreshToken database record
            
        Raises:
            HTTPException: If token is invalid, expired, or revoked
        """
        token_hash = RefreshTokenService._hash_token(raw_token)
        
        # Look up token by hash
        db_token = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
        
        if not db_token:
            logger.warning("Refresh token not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Check if revoked
        if db_token.is_revoked:
            logger.warning(f"Refresh token {db_token.id} is revoked")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
        
        # Check if expired
        if db_token.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Refresh token {db_token.id} expired at {db_token.expires_at}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )
        
        return db_token
    
    @staticmethod
    def rotate_refresh_token(
        db: Session,
        old_raw_token: str,
        days: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS,
    ) -> tuple[str, RefreshToken]:
        """
        Rotate a refresh token (invalidate old, issue new).
        
        Args:
            db: Database session
            old_raw_token: Old refresh token to rotate
            days: Days until expiration for new token
            
        Returns:
            Tuple of (new_raw_token, new_db_token)
            
        Raises:
            HTTPException: If old token is invalid
        """
        # Verify old token
        old_db_token = RefreshTokenService.verify_refresh_token(db, old_raw_token)
        
        # Revoke old token
        old_db_token.is_revoked = True
        old_db_token.revoked_at = datetime.now(timezone.utc)
        db.add(old_db_token)
        db.flush()
        
        # Create new token for same user
        user = old_db_token.user
        new_raw_token = RefreshTokenService.create_refresh_token(db, user, days)
        
        # Get new token record
        new_token_hash = RefreshTokenService._hash_token(new_raw_token)
        new_db_token = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == new_token_hash)
            .first()
        )
        
        logger.info(
            f"Rotated refresh token for user {user.id}: "
            f"old token {old_db_token.id} -> new token {new_db_token.id}"
        )
        
        # Audit log
        try:
            create_audit_log(
                db=db,
                action="refresh_token_rotated",
                user_id=user.id,
                organization_id=user.organization_id,
                metadata={
                    "old_token_id": old_db_token.id,
                    "new_token_id": new_db_token.id,
                },
            )
            db.commit()
        except Exception as audit_error:
            logger.error(f"Failed to create audit log for refresh token rotation: {audit_error}")
        
        return new_raw_token, new_db_token
    
    @staticmethod
    def revoke_refresh_token(db: Session, raw_token: str) -> None:
        """
        Revoke a refresh token (logout).
        
        Args:
            db: Database session
            raw_token: Refresh token to revoke
            
        Raises:
            HTTPException: If token is invalid
        """
        db_token = RefreshTokenService.verify_refresh_token(db, raw_token)
        
        db_token.is_revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db.add(db_token)
        db.commit()
        
        logger.info(f"Revoked refresh token {db_token.id} for user {db_token.user_id}")
        
        # Audit log
        try:
            create_audit_log(
                db=db,
                action="refresh_token_revoked",
                user_id=db_token.user_id,
                organization_id=db_token.user.organization_id,
                metadata={"token_id": db_token.id},
            )
            db.commit()
        except Exception as audit_error:
            logger.error(f"Failed to create audit log for refresh token revocation: {audit_error}")
    
    @staticmethod
    def revoke_all_user_tokens(db: Session, user: User) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            db: Database session
            user: User to revoke tokens for
            
        Returns:
            Number of tokens revoked
        """
        count = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked == False,
            )
            .update(
                {
                    "is_revoked": True,
                    "revoked_at": datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        
        db.commit()
        
        logger.info(f"Revoked {count} refresh tokens for user {user.id}")
        
        return count


# Singleton instance
refresh_token_service = RefreshTokenService()
