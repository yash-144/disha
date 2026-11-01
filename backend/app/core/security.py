import hashlib
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from app.core.config import settings

def get_password_hash(password: str) -> str:
    """Deterministic salted SHA-256 for test/local portability without C extensions."""
    salt = "disha_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = int(expire.timestamp())
    header = {"alg": "HS256", "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    signature = hashlib.sha256(f"{header_b64}.{payload_b64}.{settings.DISHA_JWT_SECRET}".encode()).hexdigest()
    return f"{header_b64}.{payload_b64}.{signature}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature = parts
        expected_sig = hashlib.sha256(f"{header_b64}.{payload_b64}.{settings.DISHA_JWT_SECRET}".encode()).hexdigest()
        if signature != expected_sig:
            return None
            
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
            
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            return None # Expired
        return payload
    except Exception:
        return None
