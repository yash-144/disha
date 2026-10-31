"""Privacy: nothing identifying a student leaves DISHA.

IDs are replaced by a salted HMAC hash; names/emails/phones are dropped.
Everything sent to Meko passes through scrub() as a second line of defence.
"""
from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any

ID_KEYS = {"student_id", "roll_no", "rollno", "enrollment_no", "enrolment_no", "user_id", "case_id"}
DROP_KEYS = {"name", "student_name", "full_name", "email", "phone", "mobile", "address",
             "dob", "date_of_birth", "parent_name", "guardian", "aadhaar", "pan"}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s-]{8,}\d(?!\w)")


def hash_id(value: Any, salt: str) -> str:
    """Stable pseudonym for an ID. Without a salt we refuse to hash (guessable)."""
    if not salt:
        return "student-unlinked"
    digest = hmac.new(salt.encode(), str(value).encode(), hashlib.sha256).hexdigest()
    return "s_" + digest[:12]


def scrub_text(text: str) -> str:
    return PHONE_RE.sub("[phone]", EMAIL_RE.sub("[email]", text))


def scrub(obj: Any, salt: str) -> Any:
    """Recursively hash ID fields, drop PII fields and mask emails/phones in strings."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key = str(k).lower()
            if key in DROP_KEYS:
                out[k] = "[redacted]"
            elif key in ID_KEYS:
                out[k] = hash_id(v, salt)
            else:
                out[k] = scrub(v, salt)
        return out
    if isinstance(obj, (list, tuple, set)):
        return [scrub(v, salt) for v in obj]
    if isinstance(obj, str):
        return scrub_text(obj)
    return obj
