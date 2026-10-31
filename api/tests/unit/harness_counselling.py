"""Shared fixture for the counselling / interventions / notifications / campus tests.

A mini FastAPI app mounts the real routers (and the cases router) on an in-memory SQLite database.
Requests carry real JWTs minted with ``create_access_token`` and are checked against real memberships,
so RBAC and tenancy go through ``get_tenancy_context`` unmodified.
"""
import sys
import uuid
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.exceptions import register_exception_handlers  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.modules.campus.models import Campus  # noqa: E402
from app.modules.cases.models import Case  # noqa: E402
from app.modules.cases.routes import router as cases_router  # noqa: E402
from app.modules.campus.routes import router as campus_router  # noqa: E402
from app.modules.counselling.routes import router as counselling_router  # noqa: E402
from app.modules.identity.models import Membership, User  # noqa: E402
from app.modules.interventions.routes import case_router, router as interventions_router  # noqa: E402
from app.modules.notifications.routes import router as notifications_router  # noqa: E402
from app.modules.roster.models import Student  # noqa: E402
from app.shared.utils import utc_now  # noqa: E402
import app.shared.idempotency_store  # noqa: E402,F401  (registers the table)

CAMPUS_A = "campus-a"
CAMPUS_B = "campus-b"


def build_app(sessionmaker) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(cases_router, prefix="/api/v1/cases")
    app.include_router(case_router, prefix="/api/v1/cases")
    app.include_router(counselling_router, prefix="/api/v1/counselling")
    app.include_router(interventions_router, prefix="/api/v1/interventions")
    app.include_router(notifications_router, prefix="/api/v1/notifications")
    app.include_router(campus_router, prefix="/api/v1/campus")

    async def _db():
        async with sessionmaker() as s:
            yield s

    app.dependency_overrides[get_db] = _db
    return app


def idem() -> dict:
    return {"X-Idempotency-Key": uuid.uuid4().hex}


class CounsellingFixture:
    """Mixin for unittest.IsolatedAsyncioTestCase."""

    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.sessionmaker = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.app = build_app(self.sessionmaker)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test")
        self.ids = {}
        async with self.sessionmaker() as s:
            s.add(Campus(id=CAMPUS_A, name="Campus A", code="A", settings={}))
            s.add(Campus(id=CAMPUS_B, name="Campus B", code="B", settings={}))
            for name, campus, role, dept in [
                ("counsellor1", CAMPUS_A, "counsellor", "Guidance"),
                ("counsellor2", CAMPUS_A, "counsellor", "Guidance"),
                ("hod", CAMPUS_A, "hod", "Guidance"),
                ("admin", CAMPUS_A, "institution_admin", None),
                ("admin2", CAMPUS_A, "institution_admin", None),
                ("faculty", CAMPUS_A, "faculty", "CS"),
                ("studentuser", CAMPUS_A, "student", None),
                ("counsellorB", CAMPUS_B, "counsellor", "Guidance"),
                ("adminB", CAMPUS_B, "institution_admin", None),
            ]:
                uid = str(uuid.uuid4())
                self.ids[name] = uid
                s.add(User(id=uid, email=f"{name}@test.local", hashed_password="x", full_name=name.title()))
                s.add(Membership(id=str(uuid.uuid4()), user_id=uid, campus_id=campus, role=role, department=dept))
            self.ids["student"] = str(uuid.uuid4())
            s.add(Student(id=self.ids["student"], campus_id=CAMPUS_A, student_uid="S-1", full_name="Student One",
                          user_id=self.ids["studentuser"], department="CS"))
            self.ids["studentB"] = str(uuid.uuid4())
            s.add(Student(id=self.ids["studentB"], campus_id=CAMPUS_B, student_uid="S-B1", full_name="Student B"))
            await s.commit()

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.engine.dispose()

    # ---- helpers
    def h(self, who: str, campus: str = CAMPUS_A, with_idem: bool = False) -> dict:
        token = create_access_token({"sub": self.ids[who]})
        headers = {"Authorization": f"Bearer {token}", "X-Campus-ID": campus}
        if with_idem:
            headers.update(idem())
        return headers

    async def make_case(self, owner="counsellor1", state="support_in_progress", due_in_hours=48,
                        campus=CAMPUS_A, student=None) -> str:
        async with self.sessionmaker() as s:
            c = Case(
                id=str(uuid.uuid4()), campus_id=campus, student_id=student or self.ids["student"],
                assigned_counsellor_id=self.ids[owner] if owner else None, status=state, title="Test case",
                due_date=utc_now() + timedelta(hours=due_in_hours) if due_in_hours is not None else None,
            )
            s.add(c)
            await s.commit()
            return c.id

    async def get_case(self, case_id: str) -> Case:
        async with self.sessionmaker() as s:
            return await s.get(Case, case_id)
