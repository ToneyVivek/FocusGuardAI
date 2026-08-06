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
    print(f"[JWT] Creating access token - subject: {subject}, user_id: {user_id}, role: {role}")
    print(f"[JWT] JWT_SECRET (first 8 chars): {settings.JWT_SECRET[:8]}")
    print(f"[JWT] JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    
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
    
    print(f"[JWT] Token payload: {to_encode}")

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    print(f"[JWT] Token encoded successfully - length: {len(encoded_jwt)}")
    return encoded_jwt
