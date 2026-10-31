from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Dedicated password hashing context supporting Argon2id (default) and bcrypt
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored hash (Argon2id or bcrypt)."""
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2id."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token using settings configuration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.DISHA_JWT_SECRET,
        algorithm=settings.DISHA_JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and cryptographically verify a JWT access token.

    Returns the decoded payload if valid and not expired; returns None otherwise.
    """
    if not token or not isinstance(token, str):
        return None
    try:
        payload = jwt.decode(
            token,
            settings.DISHA_JWT_SECRET,
            algorithms=[settings.DISHA_JWT_ALGORITHM],
            options={"require": ["exp"]},
        )
        return payload
    except (jwt.PyJWTError, Exception):
        return None
