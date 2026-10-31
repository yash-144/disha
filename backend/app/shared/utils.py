import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict


def generate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def compute_hash(data: Any, prev_hash: str = "") -> str:
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(f"{prev_hash}{content}".encode("utf-8")).hexdigest()
