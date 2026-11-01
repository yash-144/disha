"""Counselling: caseload, sessions, confidential notes, assignments. RBAC and tenancy."""
import unittest
from datetime import timedelta

from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.counselling.models import CounsellingNote
from app.modules.notifications.models import NotificationOutbox
from app.shared.utils import utc_now
from .harness_counselling import CAMPUS_A, CAMPUS_B, CounsellingFixture, idem


def when(hours):
    return (utc_now() + timedelta(hours=hours)).isoformat()


class TestCounsellingModule(CounsellingFixture, unittest.IsolatedAsyncioTestCase):

    # ------------------------------------------------------------ RBAC / tenancy
    async def test_anonymous_is_401_and_student_role_is_403(self):
        r = await self.client.get("/api/v1/counselling/caseload", headers={"X-Campus-ID": CAMPUS_A})
        self.assertEqual(r.status_code, 401)
        r = await self.client.get("/api/v1/counselling/caseload", headers=self.h("studentuser"))
        self.assertEqual(r.status_code, 403)
        r = await self.client.get("/api/v1/counselling/caseload", headers=self.h("faculty"))
        self.assertEqual(r.status_code, 403)

    async def test_user_without_membership_in_campus_is_403(self):
        r = await self.client.get("/api/v1/counselling/caseload", headers=self.h("counsellorB", CAMPUS_A))
        self.assertEqual(r.status_code, 403)

    async def test_caseload_lists_only_own_cases_in_own_campus(self):
        mine = await self.make_case("counsellor1")
        await self.make_case("counsellor2")
        await self.make_case("counsellorB", campus=CAMPUS_B, student=self.ids["studentB"])
        r = await self.client.get("/api/v1/counselling/caseload", headers=self.h("counsellor1"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual([c["case_id"] for c in r.json()], [mine])
        # a counsellor cannot ask for a colleague's caseload; the HOD can
        r = await self.client.get(f"/api/v1/counselling/caseload?counsellor_id={self.ids['counsellor2']}",
                                  headers=self.h("counsellor1"))
        self.assertEqual(r.status_code, 403)
        r = await self.client.get(f"/api/v1/counselling/caseload?counsellor_id={self.ids['counsellor2']}",
                                  headers=self.h("hod"))
        self.assertEqual(len(r.json()), 1)
        # the other campus never leaks
        r = await self.client.get("/api/v1/counselling/caseload", headers=self.h("counsellorB", CAMPUS_B))
        self.assertEqual(len(r.json()), 1)
        self.assertNotEqual(r.json()[0]["case_id"], mine)

    async def test_dashboard_counts_overdue_and_is_counsellor_only(self):
        await self.make_case("counsellor1", due_in_hours=-5)
        await self.make_case("counsellor1", due_in_hours=24)
        r = await self.client.get("/api/v1/counselling/dashboard", headers=self.h("counsellor1"))
        body = r.json()
        self.assertEqual((body["active_cases"], body["overdue_cases"]), (2, 1))
        r = await self.client.get("/api/v1/counselling/dashboard", headers=self.h("admin"))
        self.assertEqual(r.status_code, 403)

    # ------------------------------------------------------------------ profile
    async def test_profile_upsert_uses_membership_not_body(self):
        r = await self.client.get("/api/v1/counselling/profile", headers=self.h("counsellor1"))
        self.assertEqual(r.status_code, 404)
        r = await self.client.put("/api/v1/counselling/profile", headers=self.h("counsellor1"),
                                  json={"department": "Guidance", "availability_status": "away",
                                        "campus_id": CAMPUS_B, "user_id": self.ids["counsellor2"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["campus_id"], CAMPUS_A)
        self.assertEqual(r.json()["user_id"], self.ids["counsellor1"])
        self.assertEqual(r.json()["availability_status"], "away")

    # ----------------------------------------------------------------- sessions
    async def test_session_requires_caseload_scope_and_notifies_student(self):
        body = {"student_id": self.ids["student"], "scheduled_at": when(24)}
        r = await self.client.post("/api/v1/counselling/sessions", json=body, headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 403)  # not on caseload yet
        await self.make_case("counsellor1")
        r = await self.client.post("/api/v1/counselling/sessions", json=body, headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 201, r.text)
        async with self.sessionmaker() as s:
            rows = (await s.execute(select(NotificationOutbox))).scalars().all()
        self.assertEqual([(x.template_key, x.recipient_id) for x in rows],
                         [("SESSION_SCHEDULED", self.ids["studentuser"])])

    async def test_session_overlap_is_409_and_idempotent_replay_is_not(self):
        await self.make_case("counsellor1")
        body = {"student_id": self.ids["student"], "scheduled_at": when(24), "duration_minutes": 60}
        key = idem()
        r1 = await self.client.post("/api/v1/counselling/sessions", json=body, headers={**self.h("counsellor1"), **key})
        r2 = await self.client.post("/api/v1/counselling/sessions", json=body, headers={**self.h("counsellor1"), **key})
        self.assertEqual((r1.status_code, r2.status_code), (201, 201))
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        # same key, different body
        r3 = await self.client.post("/api/v1/counselling/sessions", json={**body, "duration_minutes": 30},
                                    headers={**self.h("counsellor1"), **key})
        self.assertEqual(r3.status_code, 409)
        self.assertEqual(r3.json()["details"]["code"], "IDEMPOTENCY_KEY_REUSED")
        # a different key for an overlapping slot
        r4 = await self.client.post("/api/v1/counselling/sessions", json=body, headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r4.status_code, 409)
        listing = await self.client.get("/api/v1/counselling/sessions", headers=self.h("counsellor1"))
        self.assertEqual(len(listing.json()), 1)

    async def test_missing_idempotency_key_is_rejected(self):
        r = await self.client.post("/api/v1/counselling/sessions", headers=self.h("counsellor1"),
                                   json={"student_id": self.ids["student"], "scheduled_at": when(24)})
        self.assertEqual(r.status_code, 422)

    async def test_session_lifecycle_and_ownership(self):
        await self.make_case("counsellor1")
        r = await self.client.post("/api/v1/counselling/sessions", headers=self.h("counsellor1", with_idem=True),
                                   json={"student_id": self.ids["student"], "scheduled_at": when(24)})
        sid = r.json()["id"]
        base = f"/api/v1/counselling/sessions/{sid}"
        # another counsellor cannot touch it
        self.assertEqual((await self.client.post(f"{base}/cancel", json={"reason": "x1"}, headers=self.h("counsellor2"))).status_code, 403)
        # the future session cannot be completed yet
        self.assertEqual((await self.client.post(f"{base}/complete", headers=self.h("counsellor1"))).status_code, 422)
        # reschedule, then cancel; a cancelled session is final
        r = await self.client.patch(base, json={"scheduled_at": when(48)}, headers=self.h("counsellor1"))
        self.assertEqual(r.status_code, 200)
        r = await self.client.post(f"{base}/cancel", json={"reason": "student unwell"}, headers=self.h("counsellor1"))
        self.assertEqual(r.json()["status"], "cancelled")
        self.assertEqual((await self.client.post(f"{base}/cancel", json={"reason": "again"}, headers=self.h("counsellor1"))).status_code, 422)
        self.assertEqual((await self.client.patch(base, json={"scheduled_at": when(60)}, headers=self.h("counsellor1"))).status_code, 422)
        # the other counsellor does not see it; the admin can read but not write
        self.assertEqual((await self.client.get(base, headers=self.h("counsellor2"))).status_code, 404)
        self.assertEqual((await self.client.get(base, headers=self.h("admin"))).status_code, 200)
        self.assertEqual((await self.client.post(f"{base}/complete", headers=self.h("admin"))).status_code, 403)

    async def test_past_session_can_be_completed(self):
        await self.make_case("counsellor1")
        r = await self.client.post("/api/v1/counselling/sessions", headers=self.h("counsellor1", with_idem=True),
                                   json={"student_id": self.ids["student"], "scheduled_at": when(0)})
        sid = r.json()["id"]
        r = await self.client.post(f"/api/v1/counselling/sessions/{sid}/complete", headers=self.h("counsellor1"))
        self.assertEqual(r.json()["status"], "completed")
        self.assertIsNotNone(r.json()["completed_at"])

    async def test_cross_campus_student_is_404(self):
        r = await self.client.post("/api/v1/counselling/sessions", headers=self.h("hod", with_idem=True),
                                   json={"student_id": self.ids["studentB"], "scheduled_at": when(24),
                                         "counsellor_id": self.ids["counsellor1"]})
        self.assertEqual(r.status_code, 404)

    # ------------------------------------------------------- confidential notes
    async def test_notes_are_counsellor_only_and_scoped(self):
        await self.make_case("counsellor1")
        secret = "Disclosed severe family conflict"
        r = await self.client.post("/api/v1/counselling/notes", headers=self.h("counsellor1", with_idem=True),
                                   json={"student_id": self.ids["student"], "content": secret})
        self.assertEqual(r.status_code, 201)
        url = f"/api/v1/counselling/students/{self.ids['student']}/notes"
        self.assertEqual(len((await self.client.get(url, headers=self.h("counsellor1"))).json()), 1)
        # institution admin, HOD, faculty: no access; a counsellor not on the caseload: no access
        for who in ("admin", "hod", "faculty"):
            self.assertEqual((await self.client.get(url, headers=self.h(who))).status_code, 403, who)
        self.assertEqual((await self.client.get(url, headers=self.h("counsellor2"))).status_code, 403)
        r = await self.client.post("/api/v1/counselling/notes", headers=self.h("admin", with_idem=True),
                                   json={"student_id": self.ids["student"], "content": "x"})
        self.assertEqual(r.status_code, 403)
        # another campus's counsellor cannot see the student at all
        r = await self.client.get(url, headers=self.h("counsellorB", CAMPUS_B))
        self.assertEqual(r.status_code, 404)

    async def test_note_content_never_reaches_audit_or_outbox(self):
        await self.make_case("counsellor1")
        secret = "Disclosed severe family conflict"
        await self.client.post("/api/v1/counselling/notes", headers=self.h("counsellor1", with_idem=True),
                               json={"student_id": self.ids["student"], "content": secret})
        await self.client.get(f"/api/v1/counselling/students/{self.ids['student']}/notes", headers=self.h("counsellor1"))
        async with self.sessionmaker() as s:
            audits = (await s.execute(select(AuditEvent))).scalars().all()
            actions = {a.action for a in audits}
            self.assertIn("COUNSELLING_NOTE_CREATED", actions)
            self.assertIn("COUNSELLING_NOTES_READ", actions)  # reading is audited
            self.assertNotIn(secret, " ".join(str(a.event_metadata) for a in audits))
            self.assertEqual(len((await s.execute(select(CounsellingNote))).scalars().all()), 1)

    # -------------------------------------------------------------- assignments
    async def test_assignments_admin_only_and_unlock_caseload(self):
        body = {"counsellor_id": self.ids["counsellor1"], "student_id": self.ids["student"]}
        self.assertEqual((await self.client.post("/api/v1/counselling/assignments", json=body,
                                                  headers=self.h("counsellor1", with_idem=True))).status_code, 403)
        r = await self.client.post("/api/v1/counselling/assignments", json=body, headers=self.h("hod", with_idem=True))
        self.assertEqual(r.status_code, 201)
        aid = r.json()["id"]
        # duplicate
        r = await self.client.post("/api/v1/counselling/assignments", json=body, headers=self.h("hod", with_idem=True))
        self.assertEqual(r.status_code, 409)
        # the assigned counsellor now sees the student without any case
        r = await self.client.get("/api/v1/counselling/students", headers=self.h("counsellor1"))
        self.assertEqual([s["student_ref"] for s in r.json()], ["S-1"])
        # ending the assignment removes it
        self.assertEqual((await self.client.delete(f"/api/v1/counselling/assignments/{aid}", headers=self.h("hod"))).status_code, 200)
        r = await self.client.get("/api/v1/counselling/students", headers=self.h("counsellor1"))
        self.assertEqual(r.json(), [])

    async def test_cannot_assign_non_counsellor_or_cross_campus(self):
        r = await self.client.post("/api/v1/counselling/assignments", headers=self.h("hod", with_idem=True),
                                   json={"counsellor_id": self.ids["faculty"], "student_id": self.ids["student"]})
        self.assertEqual(r.status_code, 422)
        r = await self.client.post("/api/v1/counselling/assignments", headers=self.h("hod", with_idem=True),
                                   json={"counsellor_id": self.ids["counsellor1"], "student_id": self.ids["studentB"]})
        self.assertEqual(r.status_code, 404)

    async def test_every_write_is_audited(self):
        await self.make_case("counsellor1")
        await self.client.post("/api/v1/counselling/sessions", headers=self.h("counsellor1", with_idem=True),
                               json={"student_id": self.ids["student"], "scheduled_at": when(24)})
        await self.client.put("/api/v1/counselling/profile", headers=self.h("counsellor1"), json={"phone": "1"})
        async with self.sessionmaker() as s:
            actions = {a.action for a in (await s.execute(select(AuditEvent))).scalars().all()}
        self.assertTrue({"SESSION_SCHEDULED", "PROFILE_CREATED"} <= actions)


if __name__ == "__main__":
    unittest.main()
