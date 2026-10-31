from datetime import timedelta

from sqlalchemy import select

from app.core.permissions import Role
from app.modules.audit.models import AuditEvent
from app.modules.cases.models import Case, Signal
from app.modules.policy.models import PolicyDecision
from app.modules.policy.schemas import PolicyVersionCreate, PolicyDefinition
from app.modules.policy.services import PolicyError, PolicyService, evaluate_risk_flags
from app.shared.utils import utc_now

from .phase5_support import CAMPUS_A, CAMPUS_B, DEFAULT_POLICY, DbTestCase, flag, hdr

P = "/api/v1/policy"


class PolicyBase(DbTestCase):
    async def publish(self, definition=None, campus=CAMPUS_A):
        async with self.sf() as s:
            pv = await PolicyService.create_version(s, campus, "user-admin", PolicyVersionCreate(
                definition=PolicyDefinition.model_validate(definition or DEFAULT_POLICY)))
            await PolicyService.publish_version(s, campus, "user-admin", pv.id)
            await s.commit()
            return pv.id

    async def evaluate(self, flags, **kw):
        async with self.sf() as s:
            return await evaluate_risk_flags(s, CAMPUS_A, flags, self.actor(), **kw)


class TestPolicyVersions(PolicyBase):
    async def test_rbac(self):
        body = {"definition": DEFAULT_POLICY}
        self.assertEqual((await self.client.post(f"{P}/versions", json=body)).status_code, 401)
        for role in ("student", "faculty", "counsellor", "hod", "leadership"):
            r = await self.client.post(f"{P}/versions", json=body, headers=hdr(role))
            self.assertEqual(r.status_code, 403, role)
        r = await self.client.post(f"{P}/versions", json=body, headers=hdr("institution_admin"))
        self.assertEqual(r.status_code, 201, r.text)

    async def test_lifecycle_immutability_checksum_and_audit(self):
        h = hdr("institution_admin")
        v1 = (await self.client.post(f"{P}/versions", json={"definition": DEFAULT_POLICY}, headers=h)).json()
        self.assertEqual((v1["version"], v1["status"], len(v1["checksum"])), (1, "draft", 64))
        # draft is editable and the checksum follows the definition
        edited = dict(DEFAULT_POLICY, cooldown_days=30)
        r = await self.client.patch(f"{P}/versions/{v1['id']}", json={"definition": edited}, headers=h)
        self.assertNotEqual(r.json()["checksum"], v1["checksum"])
        self.assertEqual((await self.client.post(f"{P}/versions/{v1['id']}/publish", headers=h)).json()["status"], "active")
        # published is immutable
        self.assertEqual((await self.client.patch(f"{P}/versions/{v1['id']}", json={"note": "x"}, headers=h)).status_code, 409)
        self.assertEqual((await self.client.delete(f"{P}/versions/{v1['id']}", headers=h)).status_code, 409)
        # publishing v2 retires v1
        v2 = (await self.client.post(f"{P}/versions", json={"definition": DEFAULT_POLICY}, headers=h)).json()
        await self.client.post(f"{P}/versions/{v2['id']}/publish", headers=h)
        statuses = {v["version"]: v["status"] for v in (await self.client.get(f"{P}/versions", headers=h)).json()}
        self.assertEqual(statuses, {1: "retired", 2: "active"})
        async with self.sf() as s:
            actions = [a for a in (await s.execute(select(AuditEvent.action).where(AuditEvent.campus_id == CAMPUS_A))).scalars()]
        for a in ("POLICY_VERSION_CREATED", "POLICY_VERSION_UPDATED", "POLICY_VERSION_PUBLISHED"):
            self.assertIn(a, actions)

    async def test_invalid_definition_rejected(self):
        h = hdr("institution_admin")
        bad = {"definition": {"tiers": {"critical": {}}}}
        self.assertEqual((await self.client.post(f"{P}/versions", json=bad, headers=h)).status_code, 422)

    async def test_tenancy_isolation(self):
        vid = (await self.client.post(f"{P}/versions", json={"definition": DEFAULT_POLICY}, headers=hdr("institution_admin"))).json()["id"]
        other = hdr("institution_admin", campus=CAMPUS_B)
        self.assertEqual((await self.client.get(f"{P}/versions/{vid}", headers=other)).status_code, 404)
        self.assertEqual((await self.client.post(f"{P}/versions/{vid}/publish", headers=other)).status_code, 404)
        self.assertEqual((await self.client.get(f"{P}/versions", headers=other)).json(), [])


class TestEvaluation(PolicyBase):
    async def test_no_active_policy_refuses(self):
        sid = await self.make_student()
        with self.assertRaises(PolicyError):
            await self.evaluate([flag(sid)])

    async def test_creates_case_with_evidence_signal_and_audit(self):
        await self.publish()
        sid = await self.make_student()
        res = await self.evaluate([flag(sid, "high", 0.91, reasons=[{"group": "submissions", "text": "Missed 2 of the last 3", "effect_pts": 12}])])
        self.assertEqual(res.cases_created, 1)
        d = res.decisions[0]
        self.assertEqual(d.decision, "case_created")
        self.assertEqual(d.evidence["card_type"], "ml_risk_evidence")
        self.assertEqual(len(d.digest), 64)
        async with self.sf() as s:
            case = (await s.execute(select(Case))).scalars().one()
            self.assertEqual((case.campus_id, case.student_id, case.state, case.priority), (CAMPUS_A, sid, "suggested", "high"))
            self.assertIsNotNone(case.due_date)
            sig = (await s.execute(select(Signal))).scalars().one()
            self.assertEqual(case.originating_signal_id, sig.id)
            self.assertEqual(sig.ml_tier, "high")
            ev = (await s.execute(select(AuditEvent).where(AuditEvent.action == "POLICY_EVALUATED"))).scalars().one()
            self.assertEqual(ev.event_metadata["cases_created"], 1)

    async def test_dedupe_open_case_not_reflagged(self):
        await self.publish()
        sid = await self.make_student()
        self.assertEqual((await self.evaluate([flag(sid)])).cases_created, 1)
        res = await self.evaluate([flag(sid, probability=0.99)])
        self.assertEqual(res.cases_created, 0)
        self.assertEqual(res.skipped, {"open_case_exists": 1})
        async with self.sf() as s:
            self.assertEqual(len((await s.execute(select(Case))).scalars().all()), 1)

    async def test_duplicate_in_batch_keeps_highest(self):
        await self.publish()
        sid = await self.make_student()
        res = await self.evaluate([flag(sid, "medium", 0.6, course_ref="A"), flag(sid, "high", 0.95, course_ref="B")])
        self.assertEqual(res.cases_created, 1)
        self.assertEqual(res.skipped, {"duplicate_in_batch": 1})
        created = [d for d in res.decisions if d.decision == "case_created"][0]
        self.assertEqual(created.course_ref, "B")

    async def test_cooldown_after_close_then_allowed(self):
        await self.publish()
        sid = await self.make_student()
        await self.evaluate([flag(sid)])
        async with self.sf() as s:
            case = (await s.execute(select(Case))).scalars().one()
            case.status, case.closed_at = "closed", utc_now() - timedelta(days=3)
            await s.commit()
        res = await self.evaluate([flag(sid)])
        self.assertEqual(res.skipped, {"cooldown_active": 1})
        async with self.sf() as s:
            case = (await s.execute(select(Case))).scalars().one()
            case.closed_at = utc_now() - timedelta(days=15)
            await s.commit()
        self.assertEqual((await self.evaluate([flag(sid)])).cases_created, 1)

    async def test_thresholds_and_tier_none(self):
        await self.publish()
        s1, s2, s3, s4 = [await self.make_student() for _ in range(4)]
        res = await self.evaluate([
            flag(s1, "high", 0.9), flag(s2, "medium", 0.4), flag(s3, "watch", 0.3), flag(s4, "none", 0.01),
        ])
        self.assertEqual(res.cases_created, 1)
        self.assertEqual(res.skipped, {"below_threshold": 2})
        self.assertEqual(len(res.decisions), 3)  # tier none is not recorded

    async def test_capacity_caps_keep_highest_probability(self):
        pol = dict(DEFAULT_POLICY, capacity={"max_new_cases_per_evaluation": 2})
        await self.publish(pol)
        sids = [await self.make_student() for _ in range(4)]
        probs = [0.75, 0.99, 0.85, 0.8]
        res = await self.evaluate([flag(s, "high", p) for s, p in zip(sids, probs)])
        self.assertEqual(res.cases_created, 2)
        self.assertEqual(res.skipped, {"capacity_per_evaluation": 2})
        kept = {d.student_id for d in res.decisions if d.decision == "case_created"}
        self.assertEqual(kept, {sids[1], sids[2]})

    async def test_max_open_cases_cap(self):
        await self.publish(dict(DEFAULT_POLICY, capacity={"max_open_cases": 1}))
        a, b = await self.make_student(), await self.make_student()
        res = await self.evaluate([flag(a, "high", 0.9), flag(b, "high", 0.8)])
        self.assertEqual((res.cases_created, res.skipped), (1, {"capacity_open_cases": 1}))

    async def test_tenancy_flag_for_other_campus_and_unlinked_and_foreign_student(self):
        await self.publish()
        mine = await self.make_student()
        foreign = await self.make_student(campus=CAMPUS_B)
        res = await self.evaluate([
            flag(mine, campus=CAMPUS_B), flag(None), flag(foreign), flag("does-not-exist"),
        ])
        self.assertEqual(res.cases_created, 0)
        self.assertEqual(res.skipped, {"campus_mismatch": 1, "unlinked_student": 1, "unknown_student": 2})
        async with self.sf() as s:
            self.assertEqual((await s.execute(select(Case))).scalars().all(), [])

    async def test_reason_rules_open_case_and_raise_priority(self):
        pol = dict(DEFAULT_POLICY, reason_rules=[
            {"rule_key": "engagement", "reason_groups": ["engagement"], "min_effect_pts": 5, "action": "raise_priority", "priority": "urgent"},
            {"rule_key": "watch_missed", "reason_groups": ["submissions"], "min_tier": "watch", "action": "open_case", "priority": "medium"},
        ])
        await self.publish(pol)
        a, b, c = [await self.make_student() for _ in range(3)]
        res = await self.evaluate([
            flag(a, "high", 0.9, reasons=[{"group": "engagement", "text": "t", "effect_pts": 8}]),
            flag(b, "watch", 0.2, reasons=[{"group": "submissions", "text": "t", "effect_pts": 1}]),
            flag(c, "watch", 0.2, reasons=[{"group": "score_level", "text": "t", "effect_pts": 9}]),
        ])
        self.assertEqual(res.cases_created, 2)
        async with self.sf() as s:
            cases = {c.student_id: c for c in (await s.execute(select(Case))).scalars()}
        self.assertEqual(cases[a].priority, "urgent")
        self.assertEqual(cases[b].priority, "medium")
        self.assertNotIn(c, cases)

    async def test_dry_run_writes_nothing(self):
        await self.publish()
        sid = await self.make_student()
        res = await self.evaluate([flag(sid)], dry_run=True)
        self.assertEqual((res.cases_created, res.evaluation_id, res.dry_run), (1, None, True))
        async with self.sf() as s:
            self.assertEqual((await s.execute(select(Case))).scalars().all(), [])
            self.assertEqual((await s.execute(select(PolicyDecision))).scalars().all(), [])

    async def test_evaluation_persisted_and_listed_via_api_with_rbac(self):
        await self.publish()
        sid = await self.make_student()
        await self.evaluate([flag(sid)])
        r = await self.client.get(f"{P}/evaluations", headers=hdr("institution_admin"))
        items = r.json()
        self.assertEqual((len(items), items[0]["cases_created"]), (1, 1))
        self.assertEqual((await self.client.get(f"{P}/evaluations", headers=hdr("counsellor"))).status_code, 403)
        self.assertEqual((await self.client.get(f"{P}/evaluations", headers=hdr("institution_admin", campus=CAMPUS_B))).json(), [])
        detail = await self.client.get(f"{P}/evaluations/{items[0]['id']}", headers=hdr("institution_admin"))
        self.assertEqual(detail.json()["decisions"][0]["decision"], "case_created")
        self.assertEqual((await self.client.get(f"{P}/evaluations/{items[0]['id']}", headers=hdr("institution_admin", campus=CAMPUS_B))).status_code, 404)

    async def test_dry_run_endpoint(self):
        await self.publish()
        sid = await self.make_student()
        body = {"flags": [{"student_id": sid, "tier": "high", "probability": 0.9}]}
        r = await self.client.post(f"{P}/evaluations/dry-run", json=body, headers=hdr("institution_admin"))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["cases_created"], 1)
        self.assertEqual((await self.client.post(f"{P}/evaluations/dry-run", json=body, headers=hdr("faculty"))).status_code, 403)
        async with self.sf() as s:
            self.assertEqual((await s.execute(select(Case))).scalars().all(), [])
