"""Interventions, outcomes and follow-ups attached to cases; guards read from the database."""
import unittest
from datetime import timedelta

from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.shared.utils import utc_now
from .harness_counselling import CAMPUS_A, CAMPUS_B, CounsellingFixture


def when(hours):
    return (utc_now() + timedelta(hours=hours)).isoformat()


class TestInterventionsAndFollowups(CounsellingFixture, unittest.IsolatedAsyncioTestCase):

    async def catalogue(self, name="Peer mentoring", who="admin", campus=CAMPUS_A):
        r = await self.client.post("/api/v1/interventions/catalog", json={"name": name, "category": "academic"},
                                   headers=self.h(who, campus, with_idem=True))
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["id"]

    # ---------------------------------------------------------------- catalogue
    async def test_catalogue_management_is_admin_only_and_campus_scoped(self):
        r = await self.client.post("/api/v1/interventions/catalog", json={"name": "X-test"},
                                   headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 403)
        item_id = await self.catalogue("Study skills")
        # duplicate name in the same campus
        r = await self.client.post("/api/v1/interventions/catalog", json={"name": "Study skills"},
                                   headers=self.h("admin", with_idem=True))
        self.assertEqual(r.status_code, 409)
        # staff in the same campus see it, the other campus does not, and cannot edit it
        names = [i["name"] for i in (await self.client.get("/api/v1/interventions/catalog", headers=self.h("counsellor1"))).json()]
        self.assertEqual(names, ["Study skills"])
        self.assertEqual((await self.client.get("/api/v1/interventions/catalog", headers=self.h("counsellorB", CAMPUS_B))).json(), [])
        r = await self.client.patch(f"/api/v1/interventions/catalog/{item_id}", json={"is_active": False},
                                    headers=self.h("adminB", CAMPUS_B))
        self.assertEqual(r.status_code, 404)
        # deactivated entries disappear for staff
        await self.client.patch(f"/api/v1/interventions/catalog/{item_id}", json={"is_active": False}, headers=self.h("admin"))
        self.assertEqual((await self.client.get("/api/v1/interventions/catalog", headers=self.h("counsellor1"))).json(), [])

    # ------------------------------------------------------------ interventions
    async def test_intervention_rbac_and_progress_transitions(self):
        cat = await self.catalogue()
        case_id = await self.make_case("counsellor1", state="accepted")
        url = f"/api/v1/cases/{case_id}/interventions"
        body = {"catalogue_id": cat, "description": "weekly"}
        # not the owner / supervisory admin / outsiders
        self.assertEqual((await self.client.post(url, json=body, headers=self.h("counsellor2", with_idem=True))).status_code, 403)
        self.assertEqual((await self.client.post(url, json=body, headers=self.h("admin", with_idem=True))).status_code, 403)
        self.assertEqual((await self.client.post(url, json=body, headers=self.h("studentuser", with_idem=True))).status_code, 403)
        self.assertEqual((await self.client.post(url, json=body, headers=self.h("counsellorB", CAMPUS_B, with_idem=True))).status_code, 404)
        r = await self.client.post(url, json=body, headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 201, r.text)
        iid = r.json()["id"]
        self.assertEqual(r.json()["progress"], "not_started")
        # the same intervention cannot be active twice
        self.assertEqual((await self.client.post(url, json=body, headers=self.h("counsellor1", with_idem=True))).status_code, 409)
        # the supervising admin can read
        self.assertEqual(len((await self.client.get(url, headers=self.h("admin"))).json()), 1)
        # progress: not_started -> in_progress -> completed -> (final)
        item = f"{url}/{iid}"
        self.assertEqual((await self.client.patch(item, json={"progress": "in_progress"}, headers=self.h("counsellor1"))).json()["progress"], "in_progress")
        self.assertEqual((await self.client.patch(item, json={"progress": "completed"}, headers=self.h("counsellor1"))).json()["progress"], "completed")
        self.assertEqual((await self.client.patch(item, json={"progress": "in_progress"}, headers=self.h("counsellor1"))).status_code, 422)

    async def test_intervention_not_allowed_on_closed_case_or_unknown_catalogue(self):
        cat = await self.catalogue()
        closed = await self.make_case("counsellor1", state="closed")
        r = await self.client.post(f"/api/v1/cases/{closed}/interventions", json={"catalogue_id": cat},
                                   headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 422)
        open_case = await self.make_case("counsellor1", state="accepted")
        r = await self.client.post(f"/api/v1/cases/{open_case}/interventions", json={"catalogue_id": "nope"},
                                   headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 404)

    # ----------------------------------------------------------------- follow-ups
    async def test_followup_lifecycle(self):
        case_id = await self.make_case("counsellor1")
        base = f"/api/v1/cases/{case_id}/follow-ups"
        r = await self.client.post(base, json={"title": "Check in", "scheduled_at": when(24)},
                                   headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 201, r.text)
        fid = r.json()["id"]
        self.assertEqual((await self.client.post(base, json={"title": "Check in", "scheduled_at": when(24)},
                                                  headers=self.h("counsellor2", with_idem=True))).status_code, 403)
        # reschedule, note, complete (idempotent), then no more changes
        self.assertEqual((await self.client.patch(f"{base}/{fid}", json={"scheduled_at": when(48)}, headers=self.h("counsellor1"))).status_code, 200)
        r = await self.client.post(f"{base}/{fid}/notes", json={"content": "called"}, headers=self.h("counsellor1"))
        self.assertEqual([n["content"] for n in r.json()["notes"]], ["called"])
        r = await self.client.post(f"{base}/{fid}/complete", json={"contact_status": "student_reached"}, headers=self.h("counsellor1"))
        self.assertEqual(r.json()["status"], "completed")
        r2 = await self.client.post(f"{base}/{fid}/complete", json={}, headers=self.h("counsellor1"))
        self.assertEqual(r2.json()["completed_at"], r.json()["completed_at"])
        self.assertEqual((await self.client.patch(f"{base}/{fid}", json={"scheduled_at": when(72)}, headers=self.h("counsellor1"))).status_code, 422)
        self.assertEqual((await self.client.post(f"{base}/{fid}/cancel", json={"reason": "nope"}, headers=self.h("counsellor1"))).status_code, 422)
        # admins read follow-ups but not their notes
        r = await self.client.get(base, headers=self.h("admin"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()[0]["notes"], [])
        # a follow-up id from another case or campus is a 404
        other = await self.make_case("counsellor1")
        self.assertEqual((await self.client.post(f"/api/v1/cases/{other}/follow-ups/{fid}/complete", json={}, headers=self.h("counsellor1"))).status_code, 404)

    async def test_followup_on_closed_case_is_rejected(self):
        closed = await self.make_case("counsellor1", state="closed")
        r = await self.client.post(f"/api/v1/cases/{closed}/follow-ups", json={"title": "late", "scheduled_at": when(2)},
                                   headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 422)

    # ------------------------------------------------- state machine integration
    async def transition(self, case_id, target, version, who="counsellor1", **extra):
        return await self.client.post(
            f"/api/v1/cases/{case_id}/transition",
            json={"target_state": target, "expected_version": version, "notes": "n", **extra}, headers=self.h(who))

    async def test_case_guards_come_from_follow_up_and_outcome_rows(self):
        cat = await self.catalogue()
        case_id = await self.make_case("counsellor1", state="support_in_progress")
        # a client-supplied flag is not enough
        r = await self.transition(case_id, "follow_up_due", 1, has_follow_up=True)
        self.assertEqual(r.status_code, 422, r.text)
        # a scheduled (not yet delivered) support follow-up is not enough either
        base = f"/api/v1/cases/{case_id}/follow-ups"
        fid = (await self.client.post(base, json={"title": "Session", "scheduled_at": when(-1), "follow_up_type": "support_delivered"},
                                      headers=self.h("counsellor1", with_idem=True))).json()["id"]
        self.assertEqual((await self.transition(case_id, "follow_up_due", 1)).status_code, 422)
        await self.client.post(f"{base}/{fid}/complete", json={"contact_status": "student_reached"}, headers=self.h("counsellor1"))
        r = await self.transition(case_id, "follow_up_due", 1)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["case"]["version"], 2)

        # outcome_reviewed needs an outcome row
        self.assertEqual((await self.transition(case_id, "outcome_reviewed", 2)).status_code, 422)
        iid = (await self.client.post(f"/api/v1/cases/{case_id}/interventions", json={"catalogue_id": cat},
                                      headers=self.h("counsellor1", with_idem=True))).json()["id"]
        out_url = f"/api/v1/cases/{case_id}/outcome"
        bad = await self.client.post(out_url, json={"intervention_id": iid, "completion_status": "great"},
                                     headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(bad.status_code, 422)
        self.assertEqual((await self.client.post(out_url, json={"intervention_id": iid, "completion_status": "helped"},
                                                  headers=self.h("counsellor2", with_idem=True))).status_code, 403)
        ok = await self.client.post(out_url, json={"intervention_id": iid, "completion_status": "helped", "outcome_notes": "ok"},
                                    headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(ok.status_code, 201, ok.text)
        # one outcome per intervention
        self.assertEqual((await self.client.post(out_url, json={"intervention_id": iid, "completion_status": "mixed"},
                                                  headers=self.h("counsellor1", with_idem=True))).status_code, 409)
        r = await self.transition(case_id, "outcome_reviewed", 2)
        self.assertEqual(r.status_code, 200, r.text)
        listed = (await self.client.get(f"/api/v1/cases/{case_id}/interventions", headers=self.h("counsellor1"))).json()
        self.assertEqual(listed[0]["progress"], "completed")
        self.assertEqual(listed[0]["outcome"]["completion_status"], "helped")

    async def test_changing_due_date_bumps_deadline_version(self):
        case_id = await self.make_case("counsellor1")
        before = await self.get_case(case_id)
        r = await self.client.patch(f"/api/v1/cases/{case_id}", headers=self.h("counsellor1"),
                                    json={"expected_version": 1, "due_date": when(100)})
        self.assertEqual(r.status_code, 200, r.text)
        after = await self.get_case(case_id)
        self.assertEqual(after.deadline_version, before.deadline_version + 1)

    async def test_writes_are_audited_without_outcome_notes(self):
        cat = await self.catalogue()
        case_id = await self.make_case("counsellor1", state="accepted")
        iid = (await self.client.post(f"/api/v1/cases/{case_id}/interventions", json={"catalogue_id": cat},
                                      headers=self.h("counsellor1", with_idem=True))).json()["id"]
        await self.client.post(f"/api/v1/cases/{case_id}/outcome", headers=self.h("counsellor1", with_idem=True),
                               json={"intervention_id": iid, "completion_status": "mixed", "outcome_notes": "private detail"})
        async with self.sessionmaker() as s:
            audits = (await s.execute(select(AuditEvent))).scalars().all()
        self.assertTrue({"CATALOGUE_ITEM_CREATED", "INTERVENTION_SELECTED", "OUTCOME_RECORDED"} <= {a.action for a in audits})
        self.assertNotIn("private detail", " ".join(str(a.event_metadata) for a in audits))


if __name__ == "__main__":
    unittest.main()
