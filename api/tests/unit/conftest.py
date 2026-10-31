# Lets these tests import `app` when pytest runs from the repo root (make test).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

CAMPUS, USER = "c1", "u1"


def headers(role="mentor"):
    """Request headers for the `fake_auth` fixture: a bearer marker plus the role to act as."""
    return {"Authorization": "Bearer test", "X-Test-Role": role, "X-Campus-ID": CAMPUS}


@pytest.fixture
def fake_auth():
    """Stand-in for the backend's DB-verified tenancy (used by the Meko and translate route tests only).
    No Authorization header -> 401; otherwise a TenancyContext with the X-Test-Role role on campus c1."""
    from fastapi import HTTPException, Request
    from app.core.dependencies import TenancyContext, get_current_user, get_tenancy_context
    from app.core.permissions import Role
    from app.main import app

    def _ctx(request: Request) -> TenancyContext:
        if not request.headers.get("Authorization"):
            raise HTTPException(401, "Not authenticated")
        return TenancyContext(user_id=USER, email="u1@test.local", campus_id=CAMPUS,
                              role=Role(request.headers.get("X-Test-Role", "mentor")))

    app.dependency_overrides[get_tenancy_context] = _ctx
    app.dependency_overrides[get_current_user] = _ctx
    yield
    app.dependency_overrides.pop(get_tenancy_context, None)
    app.dependency_overrides.pop(get_current_user, None)
