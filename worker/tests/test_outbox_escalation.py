"""Worker jobs against a real (in-memory SQLite) database through the API's models and services."""
import sys
import unittest
import uuid
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "api", ROOT / "worker"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.database import Base  # noqa: E402
from app.modules.cases.models import Case, CaseEvent  # noqa: E402
from app.modules.identity.models import Membership, User  # noqa: E402
from app.modules.notifications.models import Notification, NotificationOutbox  # noqa: E402
from app.modules.notifications.services import NotificationOutboxService  # noqa: E402
from app.modules.roster.models import Student  # noqa: E402
import app.shared.idempotency_store  # noqa: E402,F401
from app.shared.utils import utc_now  # noqa: E402
from jobs.deadline_escalation import run_deadline_escalation  # noqa: E402
from jobs.outbox_dispatch import run_outbox_dispatch  # noqa: E402

CAMPUS = "campus-w"


class TestWorkerJobs(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.factory = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.owner, self.hod, self.student = (str(uuid.uuid4()) for _ in range(3))
        async with self.factory() as s:
            for uid, name, role in ((self.owner, "owner", "counsellor"), (self.hod, "hod", "hod")):
                s.add(User(id=uid, email=f"{name}@w.local", hashed_password="x", full_name=name))
                s.add(Membership(user_id=uid, campus_id=CAMPUS, role=role))
            s.add(Student(id=self.student, campus_id=CAMPUS, student_uid="W1", full_name="W One"))
            await s.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_outbox_job_turns_pending_rows_into_notifications(self):
        async with self.factory() as s:
            await NotificationOutboxService.enqueue(
                s, campus_id=CAMPUS, recipient_id=self.owner, template_key="CASE_ASSIGNED",
                idempotency_key="w-1", safe_payload={"from_state": "a", "to_state": "b"}, channels=["in_app", "sms"])
            await s.commit()
        counts = await run_outbox_dispatch(factory=self.factory)
        self.assertEqual((counts["sent"], counts["deferred"]), (1, 1))
        async with self.factory() as s:
            n = (await s.execute(select(Notification))).scalars().all()
            self.assertEqual([(x.recipient_id, x.is_read) for x in n], [(self.owner, False)])
            status = {o.adapter_key: o.status for o in (await s.execute(select(NotificationOutbox))).scalars()}
        self.assertEqual(status, {"in_app": "sent", "sms": "pending"})  # no SMS provider: not faked as sent

    async def test_escalation_job_escalates_overdue_case(self):
        async with self.factory() as s:
            s.add(Case(id="c-1", campus_id=CAMPUS, student_id=self.student, assigned_counsellor_id=self.owner,
                       status="support_in_progress", title="t", due_date=utc_now() - timedelta(hours=1)))
            await s.commit()
        self.assertEqual(await run_deadline_escalation(factory=self.factory), (1, 0))
        self.assertEqual(await run_deadline_escalation(factory=self.factory), (0, 0))
        async with self.factory() as s:
            ev = (await s.execute(select(CaseEvent))).scalars().all()
            self.assertEqual([e.event_type for e in ev], ["CASE_ESCALATED"])
            out = {(o.template_key, o.recipient_id) for o in (await s.execute(select(NotificationOutbox))).scalars()}
        self.assertEqual(out, {("CASE_ESCALATION_OWNER", self.owner), ("CASE_ESCALATION_SUPERVISOR", self.hod)})
        # and the outbox job then delivers them
        self.assertEqual((await run_outbox_dispatch(factory=self.factory))["sent"], 2)


if __name__ == "__main__":
    unittest.main()
