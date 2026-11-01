"""Database access for worker jobs: reuses the API's engine, models and services.

``api/`` is put on ``sys.path`` when it is not already importable (``DISHA_API_PATH`` overrides the
default location next to ``worker/``). The session factory is the API's ``AsyncSessionLocal``, so the
worker reads the same ``DISHA_DATABASE_URL``.
"""
import os
import sys
from pathlib import Path


def _ensure_api_on_path() -> None:
    try:
        import app.core.database  # noqa: F401
        return
    except ImportError:
        pass
    candidates = [os.getenv("DISHA_API_PATH"), str(Path(__file__).resolve().parents[2] / "api"), "/app/api"]
    for c in candidates:
        if c and (Path(c) / "app").is_dir():
            sys.path.insert(0, c)
            return


_ensure_api_on_path()


def session_factory():
    from app.core.database import AsyncSessionLocal

    if AsyncSessionLocal is None:
        raise RuntimeError("SQLAlchemy is not installed; the worker cannot reach the database")
    return AsyncSessionLocal
