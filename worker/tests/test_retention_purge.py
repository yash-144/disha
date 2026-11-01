import os
import sys
import unittest
import uuid
from datetime import timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "api"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base  # noqa: E402
import app.modules.audit.models  # noqa: E402,F401
import app.modules.rewards.models  # noqa: E402,F401
from app.modules.audit.models import AuditEvent  # noqa: E402
from app.modules.cases.models import Case, Signal  # noqa: E402
from app.modules.notifications.models import Notification  # noqa: E402
from app.modules.policy.models import PolicyDecision  # noqa: E402
from app.modules.roster.models import Student  # noqa: E402
from app.modules.wellbeing.models import PulsePeriod, PulseQuestionnaire, PulseSubmission  # noqa: E402
from app.shared.utils import utc_now  # noqa: E402

try:
    from worker.jobs.retention_purge import run_retention_purge
except ImportError:
    from jobs.retention_purge import run_retention_purge

OLD, NEW = timedelta(days=400), timedelta(days=1)


class TestRetentionPurge(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool,
                                          connect_args={"check_same_thread": False})
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.sf = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        now = utc_now()
        async with self.sf() as s:
            s.add(Student(id="st1", campus_id="c1", student_uid="u1", full_name="n"))
            s.add(PulseQuestionnaire(id="q", campus_id="c1", version_key="v", questions=[], created_by="a"))
            s.add(PulsePeriod(id="p", campus_id="c1", questionnaire_id="q", label="w", starts_at=now, ends_at=now, created_by="a"))
            s.add(Signal(id="sig-old", campus_id="c1", student_id="st1", rule_key="r", created_at=now - OLD))
            s.add(Signal(id="sig-used", campus_id="c1", student_id="st1", rule_key="r", created_at=now - OLD))
            s.add(Signal(id="sig-new", campus_id="c1", student_id="st1", rule_key="r", created_at=now - NEW))
            await s.flush()
            s.add(Case(id="case1", campus_id="c1", student_id="st1", title="t", originating_signal_id="sig-used"))
            s.add(PolicyDecision(id="d-old", evaluation_id="e", campus_id="c1", tier="high", decision="skipped",
                                 reason_code="x", created_at=now - OLD))
            s.add(PolicyDecision(id="d-new", evaluation_id="e", campus_id="c1", tier="high", decision="skipped",
                                 reason_code="x", created_at=now - NEW))
            s.add(PulseSubmission(id="ps-old", campus_id="c1", student_id="st1", period_id="p", questionnaire_id="q",
                                  responses={}, dimension_scores={}, reflection_ciphertext="cipher", submitted_at=now - OLD))
            for nid, read, age in (("n-old-read", True, OLD), ("n-old-unread", False, OLD), ("n-new-read", True, NEW)):
                s.add(Notification(id=nid, recipient_id="u", campus_id="c1", notification_type="t", title="t",
                                   is_read=read, created_at=now - age))
            s.add(AuditEvent(id="aud-old", actor_id="a", campus_id="c1", entity_type="x", entity_id="y", action="Z",
                             created_at=now - OLD))
            await s.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def ids(self, model):
        async with self.sf() as s:
            return set((await s.execute(select(model.id))).scalars())

    ENV = {"DISHA_RETENTION_EVIDENCE_DAYS": "90", "DISHA_RETENTION_RESTRICTED_DAYS": "90", "DISHA_RETENTION_TELEMETRY_DAYS": "90"}

    async def test_nothing_configured_is_noop(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(await run_retention_purge(self.sf, dry_run=False), {})
        self.assertEqual(len(await self.ids(Signal)), 3)

    async def test_dry_run_reports_but_deletes_nothing(self):
        with mock.patch.dict(os.environ, self.ENV, clear=True):
            report = await run_retention_purge(self.sf)  # default is dry-run
        self.assertEqual(report["policy_decisions"], {"c1": 1})
        self.assertEqual(report["notifications_read"], {"c1": 1})
        self.assertEqual(len(await self.ids(PolicyDecision)), 2)
        self.assertEqual(len(await self.ids(Notification)), 3)
        async with self.sf() as s:
            self.assertEqual((await s.get(PulseSubmission, "ps-old")).reflection_ciphertext, "cipher")
            self.assertEqual((await s.execute(select(AuditEvent).where(AuditEvent.action == "RETENTION_PURGE"))).scalars().all(), [])

    async def test_real_purge_scoped_and_audited(self):
        with mock.patch.dict(os.environ, self.ENV, clear=True):
            await run_retention_purge(self.sf, dry_run=False)
        self.assertEqual(await self.ids(PolicyDecision), {"d-new"})
        self.assertEqual(await self.ids(Signal), {"sig-used", "sig-new"})  # case-referenced signal is kept
        self.assertEqual(await self.ids(Notification), {"n-old-unread", "n-new-read"})
        self.assertIn("aud-old", await self.ids(AuditEvent))  # audit is never purged
        async with self.sf() as s:
            self.assertIsNone((await s.get(PulseSubmission, "ps-old")).reflection_ciphertext)
            self.assertIsNotNone(await s.get(PulseSubmission, "ps-old"))  # scores stay, only the reflection goes
            ev = (await s.execute(select(AuditEvent).where(AuditEvent.action == "RETENTION_PURGE"))).scalars().one()
            self.assertEqual(ev.campus_id, "c1")
            self.assertEqual(ev.event_metadata["deleted"]["policy_decisions"], 1)

    async def test_only_configured_classes_run(self):
        with mock.patch.dict(os.environ, {"DISHA_RETENTION_TELEMETRY_DAYS": "90"}, clear=True):
            await run_retention_purge(self.sf, dry_run=False)
        self.assertEqual(len(await self.ids(PolicyDecision)), 2)
        self.assertEqual(await self.ids(Notification), {"n-old-unread", "n-new-read"})


if __name__ == "__main__":
    unittest.main()
