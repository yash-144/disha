from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from app.core.config import settings

try:
    from jose import jwt
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.DISHA_JWT_SECRET, algorithm=settings.DISHA_JWT_ALGORITHM)

except ImportError:
    import hashlib
    import base64
    import json

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return get_password_hash(plain_password) == hashed_password

    def get_password_hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        payload = data.copy()
        payload["exp"] = str(datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60)))
        return base64.b64encode(json.dumps(payload).encode()).decode()
