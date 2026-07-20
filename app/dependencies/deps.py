from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from app.config.config import settings
import logging
from app.database.session import SessionLocal
from app.models.models import User, UserRole
from app.schemas.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """Dependency to yield a SQLAlchemy database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_tenant_access(user: User, org_id: int) -> None:
    """Enforces multi-tenant isolation. Prevents cross-organization data leakage."""
    if user.organization_id is None or user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access violation: You are not authorized to access this organization's resources.",
        )


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Dependency to decode and validate JWT access token and return the authenticated User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        token_type: str = payload.get("type")

        if email is None or user_id is None or role is None or token_type != "access":
            raise credentials_exception

        token_data = TokenData(email=email, user_id=user_id, role=role)
    except JWTError:
        raise credentials_exception

    user = db.query(User).options(joinedload(User.organization)).filter(User.id == token_data.user_id, User.is_deleted == False).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency requiring the ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin privileges required",
        )
    return current_user


def get_current_admin_with_org(
    current_admin: User = Depends(get_current_admin),
) -> User:
    """Admin dependency that also enforces organization membership for tenant-scoped operations."""
    if current_admin.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin must belong to an organization to perform this action.",
        )
    return current_admin
