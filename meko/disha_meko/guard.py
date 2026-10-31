"""Deterministic PII guard for anything uploaded to Meko: emails, phone numbers, student IDs."""
from __future__ import annotations

import re

from .redact import EMAIL_RE, PHONE_RE

# CS2021-042, CS-042, ABC/2021/17, 21CSE042
ID_RE = re.compile(r"\b(?:[A-Z]{2,5}[-/]?\d{3,}(?:[-/]\d+)*|\d{2}[A-Z]{2,5}\d{2,5})\b")
PATTERNS = {"email": EMAIL_RE, "phone": PHONE_RE, "student_id": ID_RE}


class PiiFound(ValueError):
    def __init__(self, kinds: list[str]):
        super().__init__("PII detected: " + ", ".join(kinds))
        self.kinds = kinds


def as_text(data: bytes) -> str:
    """Best-effort text view (PDFs: only uncompressed text streams are visible)."""
    return data.decode("utf-8", errors="ignore") if data[:4] != b"%PDF" else data.decode("latin-1")


def find_pii(text: str) -> list[str]:
    return [k for k, rx in PATTERNS.items() if rx.search(text)]


def strip_pii(text: str) -> str:
    for k, rx in PATTERNS.items():
        text = rx.sub(f"[{k}]", text)
    return text


def check(data: bytes) -> None:
    kinds = find_pii(as_text(data))
    if kinds:
        raise PiiFound(kinds)
