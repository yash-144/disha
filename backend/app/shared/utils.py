import hashlib
from datetime import datetime, timezone

def generate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)
