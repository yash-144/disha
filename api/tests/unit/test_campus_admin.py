"""Campus administration: settings, memberships and roles, email invitations."""
import unittest
import uuid

from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.campus.models import MembershipInvite
from app.modules.campus.services import InviteService
from app.modules.identity.models import Membership, User
from .harness_counselling import CAMPUS_A, CAMPUS_B, CounsellingFixture


class TestCampusAdmin(CounsellingFixture, unittest.IsolatedAsyncioTestCase):

    async def membership_id(self, who, campus=CAMPUS_A):
        async with self.sessionmaker() as s:
            res = await s.execute(select(Membership.id).where(Membership.user_id == self.ids[who], Membership.campus_id == campus))
            return res.scalar_one()

    # ----------------------------------------------------------- access control
    async def test_admin_endpoints_reject_other_roles(self):
        for who in ("counsellor1", "hod", "faculty", "studentuser"):
            for method, url in (("get", "/api/v1/campus/memberships"), ("get", "/api/v1/campus/invitations"),
                                ("get", "/api/v1/campus/dashboard")):
                r = await getattr(self.client, method)(url, headers=self.h(who))
                self.assertEqual(r.status_code, 403, f"{who} {url}")
        r = await self.client.post("/api/v1/campus/invitations", json={"email": "a@b.co", "role": "faculty"},
                                   headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(r.status_code, 403)
        self.assertEqual((await self.client.get("/api/v1/campus/memberships")).status_code, 401)

    async def test_any_member_reads_campus_but_hod_reads_settings_only(self):
        r = await self.client.get("/api/v1/campus", headers=self.h("studentuser"))
        self.assertEqual((r.status_code, r.json()["code"]), (200, "A"))
        self.assertEqual((await self.client.get("/api/v1/campus/settings", headers=self.h("hod"))).status_code, 200)
        self.assertEqual((await self.client.get("/api/v1/campus/settings", headers=self.h("counsellor1"))).status_code, 403)

    async def test_create_campus_is_platform_admin_only(self):
        r = await self.client.post("/api/v1/campus", json={"name": "New", "code": "NEW"},
                                   headers=self.h("admin", with_idem=True))
        self.assertEqual(r.status_code, 403)

    # ---------------------------------------------------------------- settings
    async def test_settings_update_merges_validates_and_audits(self):
        r = await self.client.patch("/api/v1/campus", headers=self.h("admin"), json={
            "settings": {"escalation_levels": [{"after_hours": 0, "target": "role:hod"},
                                               {"after_hours": 48, "target": "role:institution_admin"}],
                         "notification_channels": ["email"]}})
        self.assertEqual(r.status_code, 200, r.text)
        s = r.json()["settings"]
        self.assertEqual(len(s["escalation_levels"]), 2)
        self.assertEqual(s["notification_channels"], ["email", "in_app"])  # in-app is always on
        self.assertEqual(s["followup_grace_hours"], 0)  # untouched keys survive the merge
        bad = await self.client.patch("/api/v1/campus", headers=self.h("admin"), json={
            "settings": {"escalation_levels": [{"after_hours": 48, "target": "role:hod"}, {"after_hours": 1, "target": "contact"}]}})
        self.assertEqual(bad.status_code, 422)
        bad = await self.client.patch("/api/v1/campus", headers=self.h("admin"), json={"settings": {"notification_channels": ["pigeon"]}})
        self.assertEqual(bad.status_code, 422)
        # a body cannot smuggle in other fields, and another campus is untouched
        bad = await self.client.patch("/api/v1/campus", headers=self.h("admin"), json={"settings": {"campus_id": "x"}})
        self.assertEqual(bad.status_code, 422)
        other = await self.client.get("/api/v1/campus", headers=self.h("adminB", CAMPUS_B))
        self.assertEqual(len(other.json()["settings"]["escalation_levels"]), 1)
        async with self.sessionmaker() as sess:
            audits = (await sess.execute(select(AuditEvent).where(AuditEvent.action == "CAMPUS_UPDATED"))).scalars().all()
        self.assertEqual(len(audits), 1)

    # -------------------------------------------------------------- memberships
    async def test_list_memberships_is_campus_scoped(self):
        r = await self.client.get("/api/v1/campus/memberships?role=counsellor", headers=self.h("admin"))
        self.assertEqual(sorted(m["full_name"] for m in r.json()), ["Counsellor1", "Counsellor2"])
        r = await self.client.get("/api/v1/campus/memberships", headers=self.h("adminB", CAMPUS_B))
        self.assertEqual(sorted(m["full_name"] for m in r.json()), ["Adminb", "Counsellorb"])

    async def test_role_assignment_rules(self):
        mid = await self.membership_id("faculty")
        url = f"/api/v1/campus/memberships/{mid}"
        r = await self.client.patch(url, json={"role": "mentor", "department": "Maths"}, headers=self.h("admin"))
        self.assertEqual((r.status_code, r.json()["role"], r.json()["department"]), (200, "mentor", "Maths"))
        # role is validated; platform_admin and student cannot be granted; others cannot change roles
        self.assertEqual((await self.client.patch(url, json={"role": "platform_admin"}, headers=self.h("admin"))).status_code, 422)
        self.assertEqual((await self.client.patch(url, json={"role": "student"}, headers=self.h("admin"))).status_code, 422)
        self.assertEqual((await self.client.patch(url, json={"role": "hod"}, headers=self.h("hod"))).status_code, 403)
        # student memberships are not managed here
        sid = await self.membership_id("studentuser")
        self.assertEqual((await self.client.patch(f"/api/v1/campus/memberships/{sid}", json={"is_active": False}, headers=self.h("admin"))).status_code, 403)
        # another campus's membership is invisible
        self.assertEqual((await self.client.patch(url, json={"is_active": False}, headers=self.h("adminB", CAMPUS_B))).status_code, 404)
        # deactivation takes effect on the very next request
        self.assertEqual((await self.client.get("/api/v1/notifications/unread-count", headers=self.h("faculty"))).status_code, 200)
        await self.client.patch(url, json={"is_active": False}, headers=self.h("admin"))
        self.assertEqual((await self.client.get("/api/v1/notifications/unread-count", headers=self.h("faculty"))).status_code, 403)

    async def test_cannot_edit_own_membership(self):
        own = await self.membership_id("admin")
        r = await self.client.patch(f"/api/v1/campus/memberships/{own}", json={"role": "hod"}, headers=self.h("admin"))
        self.assertEqual(r.status_code, 403)

    async def test_campus_keeps_at_least_one_active_admin(self):
        pid = str(uuid.uuid4())
        async with self.sessionmaker() as s:
            s.add(User(id=pid, email="platform@test.local", hashed_password="x", full_name="Platform"))
            s.add(Membership(id=str(uuid.uuid4()), user_id=pid, campus_id="platform", role="platform_admin"))
            await s.commit()
        self.ids["platform"] = pid
        a1, a2 = await self.membership_id("admin"), await self.membership_id("admin2")
        patch = lambda mid: self.client.patch(f"/api/v1/campus/memberships/{mid}", json={"is_active": False},
                                              headers=self.h("platform"))
        self.assertEqual((await patch(a1)).status_code, 200)   # admin2 remains
        r = await patch(a2)                                     # now the last one
        self.assertEqual(r.status_code, 409, r.text)
        # demoting the last admin is refused the same way
        r = await self.client.patch(f"/api/v1/campus/memberships/{a2}", json={"role": "hod"}, headers=self.h("platform"))
        self.assertEqual(r.status_code, 409)

    # -------------------------------------------------------------- invitations
    async def invite(self, email="New.Person@Example.com", role="faculty", **kw):
        return await self.client.post("/api/v1/campus/invitations", json={"email": email, "role": role, **kw},
                                      headers=self.h("admin", with_idem=True))

    async def test_invitation_by_email_has_no_credentials(self):
        r = await self.invite()
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        self.assertEqual((body["email"], body["status"], body["role"]), ("new.person@example.com", "pending", "faculty"))
        self.assertNotIn("token", " ".join(body.keys()).lower())
        self.assertNotIn("password", " ".join(body.keys()).lower())
        self.assertEqual([i["id"] for i in (await self.client.get("/api/v1/campus/invitations?status=pending", headers=self.h("admin"))).json()], [body["id"]])
        self.assertEqual((await self.client.get("/api/v1/campus/invitations", headers=self.h("adminB", CAMPUS_B))).json(), [])

    async def test_invitation_validation_and_duplicates(self):
        self.assertEqual((await self.invite(role="platform_admin")).status_code, 422)
        self.assertEqual((await self.invite(role="student")).status_code, 422)
        self.assertEqual((await self.invite(email="not-an-email")).status_code, 422)
        self.assertEqual((await self.invite()).status_code, 201)
        self.assertEqual((await self.invite(email="new.person@example.com")).status_code, 409)  # same email, case-insensitive
        # someone who already holds the role
        self.assertEqual((await self.invite(email="faculty@test.local", role="faculty")).status_code, 409)

    async def test_invitation_idempotent_replay(self):
        from .harness_counselling import idem
        headers = {**self.h("admin"), **idem()}
        body = {"email": "x@example.com", "role": "hod"}
        a = await self.client.post("/api/v1/campus/invitations", json=body, headers=headers)
        b = await self.client.post("/api/v1/campus/invitations", json=body, headers=headers)
        self.assertEqual((a.status_code, b.status_code, a.json()["id"] == b.json()["id"]), (201, 201, True))
        c = await self.client.post("/api/v1/campus/invitations", json={**body, "role": "faculty"}, headers=headers)
        self.assertEqual(c.status_code, 409)

    async def test_revoke(self):
        inv = (await self.invite()).json()
        r = await self.client.delete(f"/api/v1/campus/invitations/{inv['id']}", headers=self.h("adminB", CAMPUS_B))
        self.assertEqual(r.status_code, 404)
        r = await self.client.delete(f"/api/v1/campus/invitations/{inv['id']}", headers=self.h("admin"))
        self.assertEqual(r.json()["status"], "revoked")
        self.assertEqual((await self.client.delete(f"/api/v1/campus/invitations/{inv['id']}", headers=self.h("admin"))).status_code, 409)
        # a revoked invitation is not claimed at sign-in
        async with self.sessionmaker() as s:
            self.assertEqual(await InviteService.claim_for_email(s, self.ids["faculty"], "new.person@example.com"), [])

    async def test_first_sign_in_claims_matching_pending_invitations_only(self):
        inv = (await self.invite(department="Physics")).json()
        await self.invite(email="other@example.com", role="mentor")
        async with self.sessionmaker() as s:
            new_user = User(id=str(uuid.uuid4()), email="new.person@example.com", hashed_password="", full_name="New Person")
            s.add(new_user)
            await s.flush()
            created = await InviteService.claim_for_email(s, new_user.id, "New.Person@EXAMPLE.com")  # verified email, any case
            await s.commit()
            self.assertEqual([(m.campus_id, m.role, m.department, m.is_active) for m in created], [(CAMPUS_A, "faculty", "Physics", True)])
            row = (await s.execute(select(MembershipInvite).where(MembershipInvite.id == inv["id"]))).scalar_one()
            self.assertEqual(row.accepted_by, new_user.id)
            # the second claim finds nothing (single use)
            self.assertEqual(await InviteService.claim_for_email(s, new_user.id, "new.person@example.com"), [])
            actions = {a.action for a in (await s.execute(select(AuditEvent))).scalars().all()}
            self.assertIn("INVITE_ACCEPTED", actions)
        self.assertEqual([i["status"] for i in (await self.client.get("/api/v1/campus/invitations?status=accepted", headers=self.h("admin"))).json()], ["accepted"])

    async def test_expired_invitation_is_not_claimed(self):
        from datetime import timedelta
        from app.shared.utils import utc_now
        inv = (await self.invite()).json()
        async with self.sessionmaker() as s:
            row = (await s.execute(select(MembershipInvite))).scalar_one()
            row.expires_at = utc_now() - timedelta(days=1)
            await s.commit()
            self.assertEqual(await InviteService.claim_for_email(s, self.ids["faculty"], "new.person@example.com"), [])
        r = await self.client.get("/api/v1/campus/invitations?status=expired", headers=self.h("admin"))
        self.assertEqual([i["id"] for i in r.json()], [inv["id"]])

    # ---------------------------------------------------------------- dashboard
    async def test_dashboard_aggregates_current_campus_only(self):
        await self.make_case("counsellor1", due_in_hours=-3)
        await self.make_case("counsellorB", campus=CAMPUS_B, student=self.ids["studentB"], due_in_hours=-3)
        await self.invite()
        r = await self.client.get("/api/v1/campus/dashboard", headers=self.h("admin"))
        b = r.json()
        self.assertEqual((b["total_students"], b["active_cases"], b["overdue_cases"], b["pending_invites"]), (1, 1, 1, 1))
        self.assertEqual(b["staff_by_role"]["counsellor"], 2)
        self.assertEqual({w["full_name"]: w["active_cases"] for w in b["counsellor_workload"]}, {"Counsellor1": 1, "Counsellor2": 0})


if __name__ == "__main__":
    unittest.main()
