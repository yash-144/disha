"""Shared DB access: the worker reuses the API's models and services (same codebase, blueprint 07 section 6)."""
import sys
from pathlib import Path

_API = str(Path(__file__).resolve().parents[2] / "api")
if _API not in sys.path:
    sys.path.append(_API)

from app.core.database import AsyncSessionLocal  # noqa: E402


def session():
    """Fresh AsyncSession; tests patch this to point at a test database."""
    return AsyncSessionLocal()
