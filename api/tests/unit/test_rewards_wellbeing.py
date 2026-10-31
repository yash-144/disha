import asyncio
import os
from datetime import timedelta
from unittest import mock

from cryptography.fernet import Fernet
from sqlalchemy import select, text

from app.modules.rewards.models import AppendOnlyError, LedgerEntry, RewardItem
from app.modules.rewards.services import RewardsService
from app.modules.wellbeing.models import PulseSubmission
from app.modules.wellbeing.services import band_of, normalise, score_responses
from app.shared.utils import utc_now

from .phase5_support import CAMPUS_A, CAMPUS_B, DbTestCase, hdr

R = "/api/v1/rewards"
W = "/api/v1/wellbeing/pulse"
KEY = "k" * 20


def student_hdr(uid, campus=CAMPUS_A, **extra):
    return hdr("student", campus=campus, user=uid, **extra)


class TestLedger(DbTestCase):
    async def test_award_idempotent_and_balance_is_sum(self):
        sid = await self.make_student()
        async with self.sf() as s:
            e1, c1 = await RewardsService.award(s, CAMPUS_A, sid, "approved_workshop", "evt-1", "staff")
            e2, c2 = await RewardsService.award(s, CAMPUS_A, sid, "approved_workshop", "evt-1", "staff")
            await RewardsService.award(s, CAMPUS_A, sid, "approved_workshop", "evt-2", "staff")
            await s.commit()
            self.assertEqual((c1, c2, e1.id == e2.id), (True, False, True))
            self.assertEqual(await RewardsService.balance(s, CAMPUS_A, sid), 30)

    async def test_ledger_rows_cannot_be_updated_or_deleted(self):
        sid = await self.make_student()
        async with self.sf() as s:
            e, _ = await RewardsService.award(s, CAMPUS_A, sid, "verified_learning", "x", "staff")
            await s.commit()
        async with self.sf() as s:
            row = await s.get(LedgerEntry, e.id)
            row.points = 999
            with self.assertRaises(AppendOnlyError):
                await s.flush()
        async with self.sf() as s:
            row = await s.get(LedgerEntry, e.id)
            await s.delete(row)
            with self.assertRaises(AppendOnlyError):
                await s.flush()
        async with self.sf() as s:
            self.assertEqual(await RewardsService.balance(s, CAMPUS_A, sid), 10)

    async def test_award_endpoint_rbac_and_system_only_pulse(self):
        sid = await self.make_student()
        body = {"student_id": sid, "activity_key": "approved_workshop", "source_ref": "w1"}
        self.assertEqual((await self.client.post(f"{R}/awards", json=body, headers=hdr("student"))).status_code, 403)
        self.assertEqual((await self.client.post(f"{R}/awards", json=body, headers=hdr("faculty"))).status_code, 403)
        self.assertEqual((await self.client.post(f"{R}/awards", json=body, headers=hdr("institution_admin"))).status_code, 200)
        pulse = dict(body, activity_key="weekly_pulse")
        self.assertEqual((await self.client.post(f"{R}/awards", json=pulse, headers=hdr("institution_admin"))).status_code, 403)
        # other campus cannot award to this student
        self.assertEqual((await self.client.post(f"{R}/awards", json=body, headers=hdr("institution_admin", campus=CAMPUS_B))).status_code, 404)


class TestRedemption(DbTestCase):
    async def setup_world(self, balance=100, cost=60, stock=1, uid="stu-1"):
        sid = await self.make_student(user_id=uid)
        async with self.sf() as s:
            item = RewardItem(campus_id=CAMPUS_A, name="Sticker pack", cost_points=cost, stock=stock)
            s.add(item)
            await s.commit()
            iid = item.id
            if balance:
                from app.modules.rewards.models import LedgerEntry
                s.add(LedgerEntry(campus_id=CAMPUS_A, student_id=sid, entry_type="award", points=balance, idempotency_key=f"seed-bal-{uid}"))
                await s.commit()
        return sid, iid

    async def redeem(self, iid, key=KEY, uid="stu-1", campus=CAMPUS_A):
        return await self.client.post(f"{R}/redemptions", json={"item_id": iid},
                                      headers=student_hdr(uid, campus, **{"X-Idempotency-Key": key}))

    async def test_redeem_flow_and_idempotency(self):
        sid, iid = await self.setup_world()
        r = await self.redeem(iid)
        self.assertEqual(r.status_code, 201, r.text)
        again = await self.redeem(iid)
        self.assertEqual(again.json()["id"], r.json()["id"])
        bal = (await self.client.get(f"{R}/balance", headers=student_hdr("stu-1"))).json()["balance"]
        self.assertEqual(bal, 40)  # charged once
        async with self.sf() as s:
            self.assertEqual((await s.get(RewardItem, iid)).stock, 0)

    async def test_insufficient_balance_and_out_of_stock(self):
        sid, iid = await self.setup_world(balance=10)
        self.assertEqual((await self.redeem(iid)).status_code, 422)
        sid2, iid2 = await self.setup_world(balance=500, stock=0, uid="stu-2")
        self.assertEqual((await self.redeem(iid2, uid="stu-2")).status_code, 409)

    async def test_missing_idempotency_key_and_non_student(self):
        _, iid = await self.setup_world()
        r = await self.client.post(f"{R}/redemptions", json={"item_id": iid}, headers=student_hdr("stu-1"))
        self.assertIn(r.status_code, (400, 422))
        r = await self.client.post(f"{R}/redemptions", json={"item_id": iid},
                                   headers=hdr("institution_admin", **{"X-Idempotency-Key": KEY}))
        self.assertEqual(r.status_code, 403)

    async def test_student_comes_from_account_not_body_and_other_campus_blocked(self):
        _, iid = await self.setup_world()
        r = await self.client.post(f"{R}/redemptions", json={"item_id": iid, "student_id": "someone-else"},
                                   headers=student_hdr("stu-1", **{"X-Idempotency-Key": KEY}))
        self.assertEqual(r.status_code, 201)
        # a student of campus B (no profile there) cannot see or use campus A items
        await self.make_student(campus=CAMPUS_B, user_id="stu-b")
        self.assertEqual((await self.redeem(iid, key="b" * 20, uid="stu-b", campus=CAMPUS_B)).status_code, 404)

    async def test_fulfilment_rbac_and_reject_refunds_append_only(self):
        sid, iid = await self.setup_world()
        rid = (await self.redeem(iid)).json()["id"]
        url = f"{R}/redemptions/{rid}/status"
        self.assertEqual((await self.client.post(url, json={"status": "fulfilled"}, headers=student_hdr("stu-1"))).status_code, 403)
        self.assertEqual((await self.client.post(url, json={"status": "fulfilled"}, headers=hdr("institution_admin", campus=CAMPUS_B))).status_code, 404)
        self.assertEqual((await self.client.post(url, json={"status": "rejected", "note": "n/a"}, headers=hdr("institution_admin"))).json()["status"], "rejected")
        self.assertEqual((await self.client.get(f"{R}/balance", headers=student_hdr("stu-1"))).json()["balance"], 100)
        self.assertEqual((await self.client.post(url, json={"status": "fulfilled"}, headers=hdr("institution_admin"))).status_code, 409)
        async with self.sf() as s:
            self.assertEqual((await s.get(RewardItem, iid)).stock, 1)
            types = sorted((await s.execute(select(LedgerEntry.entry_type).where(LedgerEntry.student_id == sid))).scalars())
            self.assertEqual(types, ["award", "redemption", "reversal"])


class TestPulseScoring(DbTestCase):
    def test_scoring_rules(self):
        self.assertEqual([normalise(x) for x in (1, 2, 3, 4, 5)], [0, 25, 50, 75, 100])
        self.assertTrue(all(normalise(x) is None for x in (0, 6, 3.5, "3", None, True)))
        qs = [{"key": "a", "dimension": "d1"}, {"key": "b", "dimension": "d1"}, {"key": "c", "dimension": "d2"}, {"key": "e", "dimension": "d3"}]
        dims, idx = score_responses(qs, {"a": 5, "b": 4, "c": 1, "e": 9})
        self.assertEqual(dims, {"d1": 87.5, "d2": 0.0, "d3": None})  # invalid is excluded, not scored 0
        self.assertEqual(idx, 43.8)  # mean of non-null dimensions only
        self.assertEqual([band_of(x) for x in (80, 65, 50, 49.9, None)], ["strong", "positive", "needs_attention", "priority_review", None])


class TestPulseApi(DbTestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {"DISHA_REFLECTION_KEY": Fernet.generate_key().decode()})
        self._env.start()
        self.addCleanup(self._env.stop)

    async def configure(self, campus=CAMPUS_A):
        h = hdr("institution_admin", campus=campus)
        q = await self.client.post(f"{W}/questionnaires", headers=h, json={"version_key": "v1.0-weekly", "questions": [
            {"key": "q1", "dimension": "emotional_wellbeing", "text": "How are you?"},
            {"key": "q2", "dimension": "belonging_community", "text": "Do you belong?"}]})
        self.assertEqual(q.status_code, 201, q.text)
        now = utc_now()
        p = await self.client.post(f"{W}/periods", headers=h, json={
            "questionnaire_id": q.json()["id"], "label": "w1",
            "starts_at": (now - timedelta(days=1)).isoformat(), "ends_at": (now + timedelta(days=6)).isoformat()})
        self.assertEqual(p.status_code, 201, p.text)
        return p.json()["id"]

    async def submit(self, uid, responses, reflection=None, campus=CAMPUS_A):
        body = {"responses": responses}
        if reflection:
            body["reflection"] = reflection
        return await self.client.post(f"{W}/submissions", json=body, headers=student_hdr(uid, campus))

    async def test_admin_only_configuration(self):
        for role in ("student", "counsellor", "leadership"):
            r = await self.client.post(f"{W}/questionnaires", headers=hdr(role), json={"version_key": "x", "questions": [{"key": "a", "dimension": "d", "text": "t"}]})
            self.assertEqual(r.status_code, 403, role)

    async def test_submission_scoring_points_once_per_period_and_reflection_encrypted(self):
        pid = await self.configure()
        sid = await self.make_student(user_id="s1")
        r = await self.submit("s1", {"q1": 5, "q2": 3}, reflection="private words")
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual((r.json()["index_score"], r.json()["band"], r.json()["points_awarded"]), (75.0, "positive", 10))
        self.assertEqual((await self.submit("s1", {"q1": 1, "q2": 1})).status_code, 409)  # one per period
        self.assertEqual((await self.client.get(f"{W}/status", headers=student_hdr("s1"))).json()["completed"], True)
        async with self.sf() as s:
            row = (await s.execute(select(PulseSubmission))).scalars().one()
            self.assertNotIn("private words", row.reflection_ciphertext)
            self.assertEqual(await RewardsService.balance(s, CAMPUS_A, sid), 10)
        # status is the caller's own: another student has not completed
        await self.make_student(user_id="s2")
        self.assertEqual((await self.client.get(f"{W}/status", headers=student_hdr("s2"))).json()["completed"], False)

    async def test_points_do_not_depend_on_answers(self):
        await self.configure()
        sids = []
        for i, resp in enumerate(({"q1": 1, "q2": 1}, {"q1": 5, "q2": 5})):
            sids.append(await self.make_student(user_id=f"u{i}"))
            self.assertEqual((await self.submit(f"u{i}", resp)).json()["points_awarded"], 10)

    async def test_all_invalid_responses_rejected_and_reflection_needs_key(self):
        await self.configure()
        await self.make_student(user_id="s1")
        self.assertEqual((await self.submit("s1", {"q1": 9, "q2": 0})).status_code, 422)
        with mock.patch.dict(os.environ, {"DISHA_REFLECTION_KEY": ""}):
            self.assertEqual((await self.submit("s1", {"q1": 3}, reflection="x")).status_code, 503)

    async def test_no_open_period(self):
        await self.make_student(user_id="s1")
        self.assertEqual((await self.submit("s1", {"q1": 3})).status_code, 409)

    async def test_aggregate_suppressed_below_ten_then_shown(self):
        pid = await self.configure()
        for i in range(9):
            await self.make_student(user_id=f"u{i}")
            await self.submit(f"u{i}", {"q1": 5, "q2": 5})
        h = hdr("counsellor")
        d = (await self.client.get(f"{W}/aggregate", params={"period_id": pid}, headers=h)).json()
        self.assertTrue(d["suppressed"])
        self.assertIsNone(d["index_score"])
        self.assertIsNone(d["dimension_scores"])
        self.assertIsNone(d["response_count"])  # even the count is withheld
        await self.make_student(user_id="u9")
        await self.submit("u9", {"q1": 1, "q2": 1})
        d = (await self.client.get(f"{W}/aggregate", params={"period_id": pid}, headers=h)).json()
        self.assertFalse(d["suppressed"])
        self.assertEqual((d["response_count"], d["eligible_count"], d["participation_rate"]), (10, 10, 1.0))
        self.assertEqual(d["index_score"], 90.0)
        self.assertNotIn("reflection", str(d))

    async def test_department_groups_below_threshold_hidden(self):
        pid = await self.configure()
        for i in range(10):
            await self.make_student(user_id=f"u{i}", department="CS" if i < 8 else "ME")
            await self.submit(f"u{i}", {"q1": 4, "q2": 4})
        d = (await self.client.get(f"{W}/aggregate", params={"period_id": pid}, headers=hdr("leadership"))).json()
        self.assertEqual(len(d["by_department"]), 2)
        self.assertTrue(all(x["suppressed"] and x["index_score"] is None for x in d["by_department"]))  # CS(8) also < 10
        self.assertNotIn("ME", str(d["by_department"]))

    async def test_rbac_and_tenancy_on_aggregates(self):
        pid = await self.configure()
        for role in ("student", "faculty", "mentor"):
            self.assertEqual((await self.client.get(f"{W}/aggregate", params={"period_id": pid}, headers=hdr(role))).status_code, 403, role)
        r = await self.client.get(f"{W}/aggregate", params={"period_id": pid}, headers=hdr("institution_admin", campus=CAMPUS_B))
        self.assertEqual(r.status_code, 404)
        self.assertEqual((await self.client.get(f"{W}/trends", headers=hdr("institution_admin", campus=CAMPUS_B))).json(), [])

    async def test_trends_suppressed_small_period(self):
        await self.configure()
        await self.make_student(user_id="s1")
        await self.submit("s1", {"q1": 3})
        t = (await self.client.get(f"{W}/trends", headers=hdr("institution_admin"))).json()
        self.assertEqual((t[0]["suppressed"], t[0]["index_score"], t[0]["response_count"]), (True, None, None))
