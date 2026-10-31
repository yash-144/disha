"""Shared harness for the documents / anchoring / student identity / AI tests.

Builds a throwaway FastAPI app with only these routers (main.py is wired up separately), an in-memory SQLite
database, and a header-driven stand-in for get_tenancy_context (X-Test-User, X-Test-Role, X-Campus-ID).
"""
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402
from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.core.dependencies import TenancyContext, get_tenancy_context  # noqa: E402
from app.core.exceptions import register_exception_handlers  # noqa: E402
from app.core.permissions import Role  # noqa: E402
from app.modules.ai.models import AiCallLog  # noqa: E402,F401
from app.modules.ai.routes import router as ai_router  # noqa: E402
from app.modules.audit.models import AuditEvent  # noqa: E402,F401
from app.modules.cases.models import Case, CaseEvent, InterventionCatalogue  # noqa: E402,F401
from app.modules.documents.models import Document  # noqa: E402,F401
from app.modules.documents.routes import router as documents_router  # noqa: E402
from app.modules.identity.models import Membership, User  # noqa: E402,F401
from app.modules.notifications.models import Notification  # noqa: E402,F401
from app.modules.roster.models import Observation, Student  # noqa: E402,F401
from app.modules.student_identity.models import StudentIdentity, WalletChallenge  # noqa: E402,F401
from app.modules.student_identity.routes import router as identity_router  # noqa: E402

C1, C2 = "campus-1", "campus-2"
STUDENT_NAME = "Aarav Sharma"
STUDENT_EMAIL = "aarav.sharma@example.edu"
STUDENT_UID = "21CS1045"
COUNSELLOR_NAME = "Meera Iyer"

# Fixed ids so tests can refer to them
U_COUNSELLOR, U_OTHER_COUNSELLOR, U_ADMIN, U_FACULTY, U_STUDENT, U_C2_ADMIN = (
    "u-counsellor", "u-counsellor-2", "u-admin", "u-faculty", "u-student", "u-admin-c2",
)


def hdr(user: str, role: str, campus: str = C1) -> dict:
    return {"X-Test-User": user, "X-Test-Role": role, "X-Campus-ID": campus}


COUNSELLOR = hdr(U_COUNSELLOR, "counsellor")
OTHER_COUNSELLOR = hdr(U_OTHER_COUNSELLOR, "counsellor")
ADMIN = hdr(U_ADMIN, "institution_admin")
FACULTY = hdr(U_FACULTY, "faculty")
STUDENT = hdr(U_STUDENT, "student")
ADMIN_C2 = hdr(U_C2_ADMIN, "institution_admin", C2)

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


class Harness:
    """Use inside IsolatedAsyncioTestCase.asyncSetUp / asyncTearDown."""

    async def start(self):
        self.engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        self.session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.tmp = tempfile.TemporaryDirectory()
        self._saved = {k: getattr(settings, k) for k in dir(settings) if k.startswith("DISHA_")}
        settings.DISHA_DOCUMENTS_STORAGE_DIR = self.tmp.name
        settings.DISHA_DOCUMENTS_S3_BUCKET = ""

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(documents_router, prefix="/api/v1/documents")
        app.include_router(identity_router, prefix="/api/v1/student-identity")
        app.include_router(ai_router, prefix="/api/v1/ai")

        async def _db():
            async with self.session() as s:
                yield s

        def _ctx(request: Request) -> TenancyContext:
            if not request.headers.get("X-Test-User"):
                raise HTTPException(401, "Authentication token required")
            return TenancyContext(
                user_id=request.headers["X-Test-User"], email="x@test.local",
                campus_id=request.headers.get("X-Campus-ID", C1), role=Role(request.headers["X-Test-Role"]),
            )

        app.dependency_overrides[get_db] = _db
        app.dependency_overrides[get_tenancy_context] = _ctx
        self.app = app
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
        await self.seed()

    async def stop(self):
        await self.client.aclose()
        await self.engine.dispose()
        self.tmp.cleanup()
        for k, v in self._saved.items():
            setattr(settings, k, v)
        from app.modules.ai import providers
        from app.modules.documents import chain, storage
        providers.set_provider_override(None)
        chain.set_chain_client_factory(None)
        storage.set_storage_override(None)

    async def seed(self):
        async with self.session() as s:
            for uid, name in [(U_COUNSELLOR, COUNSELLOR_NAME), (U_OTHER_COUNSELLOR, "Ravi Menon"), (U_ADMIN, "Admin One"),
                              (U_FACULTY, "Fay Faculty"), (U_STUDENT, STUDENT_NAME), (U_C2_ADMIN, "Admin Two")]:
                s.add(User(id=uid, email=f"{uid}@example.edu", hashed_password="x", full_name=name))
            s.add(Student(id="stu-1", campus_id=C1, user_id=U_STUDENT, student_uid=STUDENT_UID, full_name=STUDENT_NAME, email=STUDENT_EMAIL))
            s.add(Student(id="stu-2", campus_id=C2, student_uid="X-2", full_name="Other Campus"))
            s.add(Case(id="case-1", campus_id=C1, student_id="stu-1", assigned_counsellor_id=U_COUNSELLOR, title="Attendance dip",
                       description=f"{STUDENT_NAME} ({STUDENT_UID}) can be reached at {STUDENT_EMAIL} or +91 98765 43210."))
            s.add(Case(id="case-2", campus_id=C2, student_id="stu-2", title="Other"))
            s.add(InterventionCatalogue(id="cat-1", name="Peer mentoring", category="academic", description="Pair with a senior"))
            s.add(InterventionCatalogue(id="cat-2", name="Retired option", is_active=False))
            s.add(Observation(student_id="stu-1", campus_id=C1, domain="attendance", data='{"rate": 61.5, "note": "Aarav Sharma was ill"}'))
            s.add(Observation(student_id="stu-1", campus_id=C1, domain="fee_status", data='{"overdue": 1}'))
            await s.commit()

    async def upload(self, headers=COUNSELLOR, data: bytes = PDF, content_type="application/pdf", name="report.pdf", **form):
        return await self.client.post("/api/v1/documents", headers=headers, files={"file": (name, data, content_type)}, data=form)

    async def audit_actions(self, entity_id=None):
        from sqlalchemy import select
        async with self.session() as s:
            stmt = select(AuditEvent.action)
            if entity_id:
                stmt = stmt.where(AuditEvent.entity_id == entity_id)
            return [r[0] for r in (await s.execute(stmt)).all()]


def new_id() -> str:
    return str(uuid.uuid4())
