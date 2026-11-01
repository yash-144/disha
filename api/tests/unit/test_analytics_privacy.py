import uuid
from datetime import timedelta

from app.modules.cases.models import Case, CaseEvent, FollowUp
from app.shared.privacy import suppress_distribution
from app.shared.utils import utc_now

from .phase5_support import CAMPUS_A, CAMPUS_B, DbTestCase, hdr

A = "/api/v1/analytics"


class TestSuppressionHelper(DbTestCase):
    def test_small_cells_hidden_with_complementary_suppression(self):
        cells = {c["label"]: c for c in suppress_distribution({"a": 2, "b": 9, "c": 20, "d": 0}, 5)}
        self.assertTrue(cells["a"]["suppressed"] and cells["a"]["count"] is None)
        # a lone hidden cell would be recoverable by subtraction, so the next smallest is hidden too
        self.assertTrue(cells["b"]["suppressed"])
        self.assertEqual(cells["c"]["count"], 20)
        self.assertEqual(cells["d"]["count"], 0)

    def test_nothing_hidden_when_all_large(self):
        self.assertFalse(any(c["suppressed"] for c in suppress_distribution({"a": 5, "b": 6}, 5)))


class TestAnalytics(DbTestCase):
    async def add_cases(self, n, campus=CAMPUS_A, status="support_in_progress", age_days=2, owner=None):
        ids = []
        async with self.sf() as s:
            for _ in range(n):
                sid = await self.make_student(campus=campus)
                c = Case(id=str(uuid.uuid4()), campus_id=campus, student_id=sid, status=status, title="t",
                         assigned_counsellor_id=owner, created_at=utc_now() - timedelta(days=age_days))
                s.add(c)
                ids.append(c.id)
            await s.commit()
        return ids

    def cell(self, cells, label):
        return next(c for c in cells if c["label"] == label)

    async def test_rbac(self):
        for role in ("student", "faculty", "mentor"):
            self.assertEqual((await self.client.get(f"{A}/overview", headers=hdr(role))).status_code, 403, role)
        self.assertEqual((await self.client.get(f"{A}/overview")).status_code, 401)
        for role in ("institution_admin", "counsellor", "leadership"):
            self.assertEqual((await self.client.get(f"{A}/overview", headers=hdr(role))).status_code, 200, role)

    async def test_case_counts_age_and_suppression(self):
        await self.add_cases(6, status="support_in_progress", age_days=2)
        await self.add_cases(2, status="closed", age_days=40)
        await self.add_cases(7, status="assigned", age_days=20)
        d = (await self.client.get(f"{A}/cases/summary", headers=hdr("institution_admin"))).json()
        self.assertEqual((d["total_cases"], d["open_cases"]), (15, 13))
        self.assertEqual(self.cell(d["by_state"], "assigned")["count"], 7)
        # complementary suppression: the lone small cell (closed=2) drags the next smallest down with it
        self.assertTrue(self.cell(d["by_state"], "support_in_progress")["suppressed"])
        closed = self.cell(d["by_state"], "closed")  # n=2 < 5
        self.assertTrue(closed["suppressed"] and closed["count"] is None)
        self.assertEqual(self.cell(d["open_by_age"], "0-7 days")["count"], 6)
        self.assertEqual(self.cell(d["open_by_age"], "15-30 days")["count"], 7)
        self.assertEqual(self.cell(d["open_by_age"], "31+ days")["count"], 0)

    async def test_tenancy_isolation(self):
        await self.add_cases(6, campus=CAMPUS_A)
        await self.add_cases(9, campus=CAMPUS_B)
        d = (await self.client.get(f"{A}/cases/summary", headers=hdr("counsellor", campus=CAMPUS_B))).json()
        self.assertEqual(d["total_cases"], 9)
        d = (await self.client.get(f"{A}/cases/summary", headers=hdr("counsellor"))).json()
        self.assertEqual(d["total_cases"], 6)

    async def test_time_to_first_contact_and_followups(self):
        ids = await self.add_cases(5, age_days=3)
        now = utc_now()
        async with self.sf() as s:
            for i, cid in enumerate(ids):
                s.add(CaseEvent(case_id=cid, actor_id="u", campus_id=CAMPUS_A, event_type="CONTACT_ATTEMPTED",
                                created_at=now - timedelta(days=3) + timedelta(hours=10 + i)))
                s.add(FollowUp(case_id=cid, counsellor_id="u", campus_id=CAMPUS_A, title="f",
                               scheduled_at=now - timedelta(days=1),
                               status="completed" if i < 3 else "scheduled",
                               completed_at=now - timedelta(days=1) if i < 3 else None))
            await s.commit()
        h = hdr("institution_admin")
        t = (await self.client.get(f"{A}/cases/time-to-first-contact", headers=h)).json()
        self.assertFalse(t["suppressed"])
        self.assertAlmostEqual(t["median_hours"], 12.0, places=0)
        f = (await self.client.get(f"{A}/followups/completion", headers=h)).json()
        self.assertEqual(f["completion_rate"], 0.6)

    async def test_small_group_metrics_suppressed(self):
        ids = await self.add_cases(2)
        async with self.sf() as s:
            s.add(CaseEvent(case_id=ids[0], actor_id="u", campus_id=CAMPUS_A, event_type="CONTACT_ATTEMPTED"))
            s.add(FollowUp(case_id=ids[0], counsellor_id="u", campus_id=CAMPUS_A, title="f",
                           scheduled_at=utc_now() - timedelta(days=1), status="completed", completed_at=utc_now()))
            await s.commit()
        h = hdr("leadership")
        t = (await self.client.get(f"{A}/cases/time-to-first-contact", headers=h)).json()
        self.assertTrue(t["suppressed"])
        self.assertIsNone(t["median_hours"])
        self.assertIsNone(t["cases_with_contact"])
        f = (await self.client.get(f"{A}/followups/completion", headers=h)).json()
        self.assertTrue(f["suppressed"])
        self.assertIsNone(f["completion_rate"])

    async def test_intervention_outcomes_empty_campus(self):
        d = (await self.client.get(f"{A}/interventions/outcomes", headers=hdr("institution_admin"))).json()
        self.assertEqual((d["interventions_total"], d["outcomes_recorded"]), (0, 0))
