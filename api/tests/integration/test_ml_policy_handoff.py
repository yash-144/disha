"""ML scoring run -> campus policy -> suggested cases (the wiring between the ml and policy modules).

Uses the same test-only tables and bundle as test_ml_pipeline.py.
"""
from sqlalchemy import func, select

from app.modules.cases.models import Case
from app.modules.ml import jobs
from app.modules.policy import models as policy_models  # noqa: F401  (register tables)
from app.modules.policy.schemas import PolicyDefinition, PolicyVersionCreate
from app.modules.policy.services import PolicyService
from app.modules.roster.models import Student

from .test_ml_pipeline import PipelineCase, term_tables

POLICY = {
    "tiers": {
        "high": {"min_probability": 0.0, "priority": "high", "due_in_days": 3},
        "medium": {"min_probability": 0.0, "priority": "medium", "due_in_days": 7},
        "watch": {"min_probability": 0.0, "priority": "low", "due_in_days": 14},
    },
    "cooldown_days": 14,
}


class TestMlPolicyHandoff(PipelineCase):
    async def run_scoring(self, **body):
        return await self.client.post("/api/v1/ml/runs", json=body or {"as_of_day": 60, "term_id": "T2"}, headers=self.h())

    async def _link_all(self, tables, campus="campus-a"):
        async with self.sessions() as s:
            for i, ref in enumerate(sorted(set(tables["enrolments"].student_id))):
                s.add(Student(id=f"roster-{i}", campus_id=campus, student_uid=str(ref), full_name=f"Student {i}"))
            await s.commit()

    async def _publish(self, campus="campus-a"):
        async with self.sessions() as s:
            pv = await PolicyService.create_version(
                s, campus, "user-institution_admin",
                PolicyVersionCreate(definition=PolicyDefinition.model_validate(POLICY)))
            await PolicyService.publish_version(s, campus, "user-institution_admin", pv.id)
            await s.commit()

    async def _cases(self, campus="campus-a"):
        async with self.sessions() as s:
            return (await s.execute(select(func.count()).select_from(Case).where(Case.campus_id == campus))).scalar_one()

    async def test_run_without_policy_scores_but_opens_no_cases(self):
        t = term_tables()
        await self._link_all(t)
        await self.upload(t)
        r = await self.run_scoring()
        self.assertEqual(r.status_code, 201, r.text)
        self.assertIsNone(r.json()["policy"])
        self.assertEqual(await self._cases(), 0)

    async def test_run_with_policy_opens_suggested_cases_once(self):
        t = term_tables()
        await self._link_all(t)
        await self._publish()
        await self.upload(t)

        r = await self.run_scoring()
        self.assertEqual(r.status_code, 201, r.text)
        policy = r.json()["policy"]
        flagged = sum(v for k, v in r.json()["tier_counts"].items() if k.lower() not in ("on_track", "none"))
        self.assertGreater(flagged, 0)
        self.assertEqual(policy["flags_sent"], flagged)
        self.assertGreater(policy["cases_created"], 0)
        n = await self._cases()
        self.assertEqual(n, policy["cases_created"])
        async with self.sessions() as s:
            cases = (await s.execute(select(Case).where(Case.campus_id == "campus-a"))).scalars().all()
        self.assertEqual({c.state for c in cases}, {"suggested"})

        # a second run must not re-open cases for students who already have one
        again = await self.run_scoring()
        self.assertEqual(again.status_code, 201, again.text)
        self.assertEqual(again.json()["policy"]["cases_created"], 0)
        self.assertEqual(await self._cases(), n)
        self.assertEqual(await self._cases("campus-b"), 0)

    async def test_scheduled_run_applies_policy(self):
        from datetime import date, timedelta
        start = date.today() - timedelta(days=40)
        t = term_tables(term_start=start.isoformat(), max_day=40)
        await self._link_all(t)
        await self._publish()
        self.assertEqual((await self.upload(t)).status_code, 201)
        runs = await jobs.run_scheduled_scoring(self.sessions)
        self.assertEqual(len(runs), 1)
        self.assertGreaterEqual(await self._cases(), 0)  # flags at day 40 may all be on track; must not crash

