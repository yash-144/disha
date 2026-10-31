import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    # Use SHA-256 with salt for lightweight portable authentication
    salt = settings.DISHA_JWT_SECRET[:16]
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.DISHA_JWT_SECRET, algorithm=settings.DISHA_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.DISHA_JWT_SECRET,
        algorithms=[settings.DISHA_JWT_ALGORITHM]
    )
