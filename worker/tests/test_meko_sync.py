import sys
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "api"))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base  # noqa: E402
import app.modules.audit.models  # noqa: E402,F401
from app.modules.cases.models import Case, Intervention, InterventionCatalogue, InterventionOutcome, Signal  # noqa: E402
from app.shared.utils import utc_now  # noqa: E402

try:
    from worker.jobs import meko_sync
except ImportError:
    from jobs import meko_sync


class TestMekoSync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool,
                                          connect_args={"check_same_thread": False})
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.sf = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        now = utc_now()
        async with self.sf() as s:
            s.add(Signal(id="sg", campus_id="c1", student_id="st1", rule_key="r", ml_tier="high"))
            s.add(InterventionCatalogue(id="cat", name="Mentor call"))
            await s.flush()
            s.add(Case(id="k1", campus_id="c1", student_id="st1", title="t", originating_signal_id="sg"))
            s.add(Case(id="k2", campus_id="c1", student_id="st1", title="t"))
            await s.flush()
            for iv, case in (("i1", "k1"), ("i2", "k2")):
                s.add(Intervention(id=iv, case_id=case, catalogue_id="cat", counsellor_id="u", campus_id="c1"))
            await s.flush()
            s.add(InterventionOutcome(id="o1", case_id="k1", intervention_id="i1", counsellor_id="u", campus_id="c1",
                                      completion_status="helped", completed_at=now))
            s.add(InterventionOutcome(id="o2", case_id="k2", intervention_id="i2", counsellor_id="u", campus_id="c1",
                                      completion_status="mixed", completed_at=now - timedelta(days=30)))
            await s.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_weekly_outcomes_are_aggregates_only(self):
        rows = await meko_sync.fetch_weekly_outcomes(factory=self.sf)
        self.assertEqual(rows, [{"type": "Mentor call", "outcome": "helped", "tier": "high"}])

    async def test_job_survives_failures(self):
        client = mock.Mock(active=True, remember=mock.AsyncMock())
        with mock.patch.object(meko_sync, "MekoClient", lambda component: client), \
                mock.patch.object(meko_sync, "fetch_weekly_outcomes", side_effect=RuntimeError("db down")):
            await meko_sync.run_meko_weekly_outcomes()
        client.remember.assert_not_called()
