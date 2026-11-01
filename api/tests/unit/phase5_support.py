"""Shared harness for the policy / analytics / wellbeing / rewards tests.

Builds a throwaway FastAPI app with only these routers (main.py is owned elsewhere), an in-memory
SQLite database, and a header-driven stand-in for DB-verified tenancy:
X-Test-Role, X-Test-User, X-Campus-ID.
"""
import unittest
import uuid
from types import SimpleNamespace

import httpx
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.dependencies import TenancyContext, get_current_user, get_tenancy_context
from app.core.exceptions import register_exception_handlers
from app.core.permissions import Role
from app.modules.analytics.routes import router as analytics_router
from app.modules.policy.routes import router as policy_router
from app.modules.rewards.routes import router as rewards_router
from app.modules.wellbeing.routes import router as wellbeing_router
# Import every model so create_all builds all tables.
import app.modules.cases.models  # noqa: F401
import app.modules.audit.models  # noqa: F401
import app.modules.notifications.models  # noqa: F401
import app.modules.policy.models  # noqa: F401
import app.modules.wellbeing.models  # noqa: F401
import app.modules.rewards.models  # noqa: F401
from app.modules.roster.models import Student

CAMPUS_A = "campus-a"
CAMPUS_B = "campus-b"


def build_app(session_factory) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(policy_router, prefix="/api/v1/policy")
    app.include_router(analytics_router, prefix="/api/v1/analytics")
    app.include_router(wellbeing_router, prefix="/api/v1/wellbeing")
    app.include_router(rewards_router, prefix="/api/v1/rewards")

    async def _db():
        async with session_factory() as s:
            yield s

    def _ctx(request: Request) -> TenancyContext:
        role = request.headers.get("X-Test-Role")
        if not role:
            raise HTTPException(401, "Not authenticated")
        return TenancyContext(
            user_id=request.headers.get("X-Test-User", f"user-{role}"), email=f"{role}@t.local",
            campus_id=request.headers.get("X-Campus-ID", CAMPUS_A), role=Role(role),
            is_platform_admin=(role == "platform_admin"),
        )

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_tenancy_context] = _ctx
    app.dependency_overrides[get_current_user] = _ctx
    return app


def hdr(role, campus=CAMPUS_A, user=None, **extra):
    h = {"X-Test-Role": role, "X-Campus-ID": campus}
    if user:
        h["X-Test-User"] = user
    h.update(extra)
    return h


class DbTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:", poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.sf = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.app = build_app(self.sf)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://t")

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.engine.dispose()

    async def make_student(self, campus=CAMPUS_A, user_id=None, department="CS", active=True) -> str:
        sid = str(uuid.uuid4())
        async with self.sf() as s:
            s.add(Student(id=sid, campus_id=campus, user_id=user_id, student_uid=f"uid-{sid[:8]}",
                          full_name="Test Student", department=department, is_active=active))
            await s.commit()
        return sid

    @staticmethod
    def actor(role=Role.INSTITUTION_ADMIN, user_id="user-admin"):
        return SimpleNamespace(user_id=user_id, role=role, is_platform_admin=False)


def flag(student_id, tier="high", probability=0.9, campus=CAMPUS_A, reasons=None, **kw):
    return SimpleNamespace(
        campus_id=campus, student_id=student_id, external_student_ref_hash=kw.get("ref", "h" * 16),
        course_ref=kw.get("course_ref", "CS101"), as_of=kw.get("as_of", None), tier=tier, probability=probability,
        reasons=reasons if reasons is not None else [], model_version="rolling-1", score_id=kw.get("score_id", "sc-1"),
    )


DEFAULT_POLICY = {
    "tiers": {
        "high": {"min_probability": 0.7, "priority": "high", "due_in_days": 3},
        "medium": {"min_probability": 0.5, "priority": "medium", "due_in_days": 7},
    },
    "cooldown_days": 14,
}
