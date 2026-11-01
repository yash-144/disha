"""Meko wiring for the API: one client per app (lifespan) and fire-and-forget helpers.

disha_meko is optional (`pip install -e ../meko`). Without it, or without
MEKO_API_KEY, every call here is a silent no-op.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Request

try:
    from disha_meko import MekoClient
except ImportError:
    MekoClient = None

log = logging.getLogger("disha.meko")


class _Off:
    """Stand-in when disha_meko is not installed."""
    active = False
    last_error = "disha_meko package not installed"

    class cfg:
        datapack = "disha"
        url = ""
        promote_min = 3

    def hash_id(self, value):
        return "student-unlinked"

    async def _noop(self, *a, **kw):
        return None

    remember = recall = trace_decision = list_tools = mapping = ensure_datapack = save_artifact = token_usage = _noop
    upload_bytes = search_knowledge = search_memories = delete_document = promote = _noop


@asynccontextmanager
async def meko_lifespan(app: FastAPI):
    app.state.meko = MekoClient(component="disha-api") if MekoClient else _Off()
    log.info("Meko %s", "active" if app.state.meko.active else "inactive (no MEKO_API_KEY or disabled)")
    yield


def get_meko(request: Request):
    return request.app.state.meko


async def _safe(coro):
    try:
        await coro
    except Exception as exc:  # noqa: BLE001 - Meko must never surface to the caller
        log.warning("Meko background call failed: %s", exc)


def fire_and_forget(tasks: BackgroundTasks, coro) -> None:
    """Run a Meko coroutine after the response is sent."""
    tasks.add_task(_safe, coro)


def catalog_path() -> str:
    """Campus intervention catalogue (JSON). No built-in fallback catalogue (AI-07)."""
    import os
    return os.getenv("MEKO_CATALOG_PATH", "")


def catalog_entries() -> list:
    try:
        from disha_meko.catalog import load_catalog
    except ImportError:
        return []
    return load_catalog(catalog_path())
