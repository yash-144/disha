"""Case decisions and outcomes feed Meko with hashed ids; Meko failures never surface."""
import json
import unittest

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
import app.modules.audit.models  # noqa: F401
from app.modules.cases.models import Case, Intervention, InterventionCatalogue, Signal
from app.modules.meko import hooks

PACKET = json.dumps({"items": [{"metric_key": "risk_probability", "source": "ml_model"},
                               {"metric_key": "attendance", "source": "ml_reason", "text": "Jane Roe attendance"}]})


class FakeMeko:
    active = True

    def __init__(self, boom=False):
        self.traces, self.boom = [], boom

    def hash_id(self, v):
        return "s_hashed"

    async def trace_decision(self, **kw):
        if self.boom:
            raise RuntimeError("meko down")
        self.traces.append(kw)
        return True

    async def recall(self, q, k=3):
        if self.boom:
            raise RuntimeError("meko down")
        return "mentor calls helped"


async def run_tasks(tasks: BackgroundTasks):
    for t in tasks.tasks:
        await t.func(*t.args, **t.kwargs)


class TestMekoHooks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool,
                                          connect_args={"check_same_thread": False})
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.sf = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.sf() as s:
            s.add(Signal(id="sig1", campus_id="c1", student_id="RAW-STUDENT-9", rule_key="ml_risk_high",
                         ml_tier="high", evidence_snapshot=PACKET))
            s.add(InterventionCatalogue(id="cat1", campus_id=None, name="Mentor call"))
            s.add(InterventionCatalogue(id="cat2", campus_id="c1", name="Old", is_active=False))
            await s.flush()
            s.add(Case(id="case1", campus_id="c1", student_id="RAW-STUDENT-9", title="t", originating_signal_id="sig1"))
            s.add(Case(id="case2", campus_id="c1", student_id="RAW-STUDENT-9", title="manual"))
            await s.flush()
            s.add(Intervention(id="iv1", case_id="case1", catalogue_id="cat1", counsellor_id="u", campus_id="c1"))
            await s.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_decision_trace_has_hashed_student_only(self):
        meko, tasks = FakeMeko(), BackgroundTasks()
        async with self.sf() as db:
            await hooks.schedule_case_decision(tasks, meko, db, case_id="case1", action="accept", role="counsellor", campus_id="c1")
        await run_tasks(tasks)
        self.assertEqual(len(meko.traces), 1)
        t = meko.traces[0]
        self.assertEqual(t["evidence"]["student_id"], "s_hashed")
        self.assertEqual(t["evidence"]["reason_codes"], ["ATTENDANCE"])
        self.assertNotIn("RAW-STUDENT-9", json.dumps(t))
        self.assertNotIn("Jane Roe", json.dumps(t))

    async def test_manual_case_is_not_traced(self):
        meko, tasks = FakeMeko(), BackgroundTasks()
        async with self.sf() as db:
            await hooks.schedule_case_decision(tasks, meko, db, case_id="case2", action="dismiss", role="hod", campus_id="c1")
        self.assertEqual(tasks.tasks, [])

    async def test_meko_failure_never_raises(self):
        meko, tasks = FakeMeko(boom=True), BackgroundTasks()
        async with self.sf() as db:
            await hooks.schedule_case_decision(tasks, meko, db, case_id="case1", action="dismiss", role="hod", campus_id="c1")
            await run_tasks(tasks)  # fire_and_forget swallows the error
            self.assertEqual(await hooks.playbook_text(meko, db, "case1"), "")

    async def test_outcome_uses_catalogue_id_and_signal_facts(self):
        calls, tasks = [], BackgroundTasks()

        async def fake_record(client, **kw):
            calls.append(kw)

        orig = hooks.pb
        hooks.pb = type("PB", (), {"record_outcome": staticmethod(fake_record)})
        try:
            async with self.sf() as db:
                await hooks.schedule_case_outcome(tasks, FakeMeko(), db, case_id="case1", intervention_id="iv1",
                                                  completion_status="helped", campus_id="c1")
                await hooks.schedule_case_outcome(tasks, FakeMeko(), db, case_id="case1", intervention_id="iv1",
                                                  completion_status="unknown", campus_id="c1")
            await run_tasks(tasks)
        finally:
            hooks.pb = orig
        self.assertEqual(len(calls), 1)
        self.assertEqual((calls[0]["intervention_id"], calls[0]["outcome"], calls[0]["tier"], calls[0]["reason_codes"]),
                         ("cat1", "improved", "high", ["ATTENDANCE"]))
        self.assertNotIn("RAW-STUDENT-9", json.dumps(calls[0]))

    async def test_catalogue_has(self):
        async with self.sf() as db:
            self.assertTrue(await hooks.catalogue_has(db, "c1", "cat1"))
            self.assertFalse(await hooks.catalogue_has(db, "c1", "cat2"))  # inactive
            self.assertFalse(await hooks.catalogue_has(db, "c1", "nope"))
        async with self.engine.begin() as conn:
            await conn.execute(InterventionCatalogue.__table__.delete())
        async with self.sf() as db:
            self.assertIsNone(await hooks.catalogue_has(db, "c1", "cat1"))  # no rows: caller falls back to file

    async def test_playbook_text(self):
        async with self.sf() as db:
            self.assertEqual(await hooks.playbook_text(FakeMeko(), db, "case1"), "mentor calls helped")
            off = FakeMeko()
            off.active = False
            self.assertEqual(await hooks.playbook_text(off, db, "case1"), "")
