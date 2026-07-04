from datetime import timedelta, datetime, timezone
from typing import Any, Union, Optional
import bcrypt
from jose import jwt

from app.config.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain text password matches its hashed equivalent using bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt hash of a plain text password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(
    subject: Union[str, Any],
    role: str,
    user_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed JWT access token containing subject, user_id, role, and type claims."""
    now = datetime.now(timezone.utc)
    expire = now + expires_delta if expires_delta else now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    role_value = role.value if hasattr(role, "value") else str(role)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role_value,
        "user_id": int(user_id),
        "type": "access",
    }

    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
