"""Notification outbox dispatch, in-app inbox, and deadline escalation."""
import os
import unittest
import uuid
from datetime import timedelta
from unittest.mock import patch

from sqlalchemy import select

from app.core.config import settings
from app.modules.audit.models import AuditEvent
from app.modules.campus.models import Campus
from app.modules.cases.escalation import scan_and_escalate
from app.modules.cases.models import CaseEvent, FollowUp
from app.modules.cases.schemas import CaseCreateRequest
from app.modules.cases.services import CaseService
from app.modules.notifications.dispatch import process_outbox_batch
from app.modules.notifications.models import Notification, NotificationOutbox, OutboxDeliveryAttempt
from app.modules.notifications.providers import (
    DeliveryError,
    DeliveryProvider,
    InAppProvider,
    default_registry,
)
from app.modules.notifications.services import NotificationOutboxService
from app.shared.utils import utc_now
from .harness_counselling import CAMPUS_A, CAMPUS_B, CounsellingFixture


class FlakyProvider(DeliveryProvider):
    key = "in_app"

    def __init__(self):
        self.calls = 0

    def is_configured(self):
        return True

    async def send(self, db, row):
        self.calls += 1
        raise DeliveryError("PROVIDER_DOWN")


async def rows(session, model):
    return list((await session.execute(select(model))).scalars().all())


class TestOutboxDispatch(CounsellingFixture, unittest.IsolatedAsyncioTestCase):

    async def enqueue(self, s, recipient="counsellor1", channels=("in_app",), key=None, **kw):
        out = await NotificationOutboxService.enqueue(
            s, campus_id=CAMPUS_A, recipient_id=self.ids[recipient], template_key=kw.pop("template", "CASE_ASSIGNED"),
            idempotency_key=key or f"k-{uuid.uuid4()}", safe_payload={"from_state": "action_planned", "to_state": "assigned"},
            channels=list(channels), **kw,
        )
        await s.commit()
        return out

    async def test_case_assignment_writes_outbox_not_notification(self):
        async with self.sessionmaker() as s:
            await CaseService.create_case(
                s, CAMPUS_A, self.ids["admin"], ["institution_admin"],
                CaseCreateRequest(student_id=self.ids["student"], title="t", assigned_counsellor_id=self.ids["counsellor1"]),
            )
            await s.commit()
            self.assertEqual(len(await rows(s, Notification)), 0)
            outbox = await rows(s, NotificationOutbox)
            self.assertEqual([(o.status, o.adapter_key, o.template_key) for o in outbox], [("pending", "in_app", "CASE_ASSIGNED")])

    async def test_dispatch_delivers_in_app_and_is_idempotent(self):
        async with self.sessionmaker() as s:
            await self.enqueue(s, key="case-1-v1-assigned")
            counts = await process_outbox_batch(s)
            self.assertEqual(counts["sent"], 1)
            notifs = await rows(s, Notification)
            self.assertEqual(len(notifs), 1)
            n = notifs[0]
            self.assertEqual((n.recipient_id, n.campus_id, n.title, n.is_read), (self.ids["counsellor1"], CAMPUS_A, "New Case Assigned", False))
            self.assertEqual(n.idempotency_key, "case-1-v1-assigned")
            ob = (await rows(s, NotificationOutbox))[0]
            self.assertEqual((ob.status, ob.attempts), ("sent", 1))
            self.assertIsNotNone(ob.sent_at)
            attempts = await rows(s, OutboxDeliveryAttempt)
            self.assertEqual([(a.outcome, a.provider_message_id) for a in attempts], [("sent", n.id)])
            # a second run finds nothing, and re-enqueueing the same key is a no-op
            self.assertEqual((await process_outbox_batch(s))["sent"], 0)
            self.assertEqual(await self.enqueue(s, key="case-1-v1-assigned"), [])

    async def test_unconfigured_email_stays_pending_and_warns(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DISHA_SMTP_HOST", None)
            os.environ.pop("DISHA_SMTP_FROM", None)
            async with self.sessionmaker() as s:
                await self.enqueue(s, channels=("in_app", "email", "sms"), key="multi")
                with self.assertLogs("disha.notifications.dispatch", level="WARNING") as logs:
                    counts = await process_outbox_batch(s)
                self.assertEqual((counts["sent"], counts["deferred"]), (1, 2))
                by_adapter = {o.adapter_key: o for o in await rows(s, NotificationOutbox)}
                self.assertEqual(by_adapter["in_app"].status, "sent")
                for key in ("email", "sms"):
                    self.assertEqual(by_adapter[key].status, "pending")  # never marked sent
                    self.assertIsNone(by_adapter[key].sent_at)
                    self.assertEqual(by_adapter[key].attempts, 0)
                    self.assertGreater(by_adapter[key].next_attempt_at.replace(tzinfo=None), utc_now().replace(tzinfo=None))
                self.assertTrue(any("email" in m for m in logs.output))
                self.assertEqual(len(await rows(s, Notification)), 1)

    async def test_unknown_adapter_and_template_are_dead_lettered(self):
        async with self.sessionmaker() as s:
            await self.enqueue(s, channels=("pigeon",), key="odd")
            await self.enqueue(s, template="NOT_A_TEMPLATE", key="odd2")
            counts = await process_outbox_batch(s)
            self.assertEqual(counts["dead_letter"], 2)
            by_key = {o.idempotency_key: o for o in await rows(s, NotificationOutbox)}
            self.assertEqual(by_key["odd:pigeon"].last_error_code, "UNKNOWN_ADAPTER")
            self.assertEqual(by_key["odd2"].last_error_code, "UNKNOWN_TEMPLATE")
            self.assertEqual(len(await rows(s, Notification)), 0)

    async def test_failures_back_off_then_dead_letter_then_admin_retry(self):
        provider = FlakyProvider()
        async with self.sessionmaker() as s:
            await self.enqueue(s, key="flaky")
            now = utc_now()
            for attempt in range(1, settings.DISHA_OUTBOX_MAX_ATTEMPTS + 1):
                counts = await process_outbox_batch(s, registry={"in_app": provider}, now=now)
                ob = (await rows(s, NotificationOutbox))[0]
                self.assertEqual(ob.attempts, attempt)
                if attempt < settings.DISHA_OUTBOX_MAX_ATTEMPTS:
                    self.assertEqual((ob.status, counts["retry"]), ("pending", 1))
                    wait = settings.DISHA_OUTBOX_BASE_BACKOFF_SECONDS * 2 ** (attempt - 1)
                    self.assertEqual(int((ob.next_attempt_at.replace(tzinfo=None) - now.replace(tzinfo=None)).total_seconds()), wait)
                    # not due yet: skipped
                    self.assertEqual(sum((await process_outbox_batch(s, registry={"in_app": provider}, now=now)).values()), 0)
                    now = now + timedelta(seconds=wait + 1)
            self.assertEqual(ob.status, "dead_letter")
            self.assertEqual(ob.last_error_code, "PROVIDER_DOWN")
            self.assertEqual(provider.calls, settings.DISHA_OUTBOX_MAX_ATTEMPTS)
            ob_id = ob.id

        # only institution admins of that campus can see and retry it
        self.assertEqual((await self.client.get("/api/v1/notifications/outbox?status=dead_letter", headers=self.h("counsellor1"))).status_code, 403)
        listed = await self.client.get("/api/v1/notifications/outbox?status=dead_letter", headers=self.h("admin"))
        self.assertEqual([i["id"] for i in listed.json()], [ob_id])
        self.assertEqual((await self.client.get("/api/v1/notifications/outbox", headers=self.h("adminB", CAMPUS_B))).json(), [])
        self.assertEqual((await self.client.post(f"/api/v1/notifications/outbox/{ob_id}/retry", headers=self.h("adminB", CAMPUS_B))).status_code, 404)
        r = await self.client.post(f"/api/v1/notifications/outbox/{ob_id}/retry", headers=self.h("admin"))
        self.assertEqual((r.json()["status"], r.json()["attempts"]), ("pending", 0))
        async with self.sessionmaker() as s:
            await process_outbox_batch(s, registry={"in_app": InAppProvider()})
            self.assertEqual((await rows(s, NotificationOutbox))[0].status, "sent")

    # --------------------------------------------------------------- inbox API
    async def test_inbox_is_per_user_and_per_campus(self):
        async with self.sessionmaker() as s:
            for i in range(3):
                await self.enqueue(s, key=f"mine-{i}")
            await self.enqueue(s, recipient="counsellor2", key="theirs")
            await process_outbox_batch(s)
        r = await self.client.get("/api/v1/notifications?limit=2", headers=self.h("counsellor1"))
        body = r.json()
        self.assertEqual(len(body["items"]), 2)
        self.assertIsNotNone(body["next_cursor"])
        r2 = await self.client.get(f"/api/v1/notifications?limit=2&cursor={body['next_cursor']}", headers=self.h("counsellor1"))
        self.assertEqual(len(r2.json()["items"]), 1)
        self.assertIsNone(r2.json()["next_cursor"])
        ids = {i["id"] for i in body["items"]} | {i["id"] for i in r2.json()["items"]}
        self.assertEqual(len(ids), 3)
        self.assertEqual((await self.client.get("/api/v1/notifications/unread-count", headers=self.h("counsellor1"))).json(), {"unread": 3})

        # reading: own only; another user's id looks like a missing one
        one = next(iter(ids))
        self.assertEqual((await self.client.patch(f"/api/v1/notifications/{one}/read", headers=self.h("counsellor2"))).status_code, 404)
        self.assertEqual((await self.client.patch(f"/api/v1/notifications/{one}/read", headers=self.h("counsellor1"))).json()["is_read"], True)
        self.assertEqual((await self.client.get("/api/v1/notifications/unread-count", headers=self.h("counsellor1"))).json(), {"unread": 2})
        unread = await self.client.get("/api/v1/notifications?unread_only=true", headers=self.h("counsellor1"))
        self.assertEqual(len(unread.json()["items"]), 2)
        self.assertEqual((await self.client.post("/api/v1/notifications/read-all", headers=self.h("counsellor1"))).json(), {"unread": 0})
        self.assertEqual((await self.client.get("/api/v1/notifications/unread-count", headers=self.h("counsellor2"))).json(), {"unread": 1})
        self.assertEqual((await self.client.get("/api/v1/notifications")).status_code, 401)

    async def test_campus_channel_setting_adds_email_rows(self):
        async with self.sessionmaker() as s:
            camp = await s.get(Campus, CAMPUS_A)
            camp.settings = {"notification_channels": ["email"]}
            await s.commit()
            out = await NotificationOutboxService.enqueue(
                s, campus_id=CAMPUS_A, recipient_id=self.ids["counsellor1"], template_key="CASE_ASSIGNED", idempotency_key="chan")
            self.assertEqual(sorted(o.adapter_key for o in out), ["email", "in_app"])


class TestEscalation(CounsellingFixture, unittest.IsolatedAsyncioTestCase):

    async def set_levels(self, levels, contact=None):
        async with self.sessionmaker() as s:
            camp = await s.get(Campus, CAMPUS_A)
            camp.settings = {"escalation_levels": levels, "escalation_contact_user_id": contact}
            await s.commit()

    async def scan(self, now=None):
        async with self.sessionmaker() as s:
            return await scan_and_escalate(s, now)

    async def test_overdue_case_escalates_once_and_notifies(self):
        overdue = await self.make_case("counsellor1", due_in_hours=-2)
        future = await self.make_case("counsellor1", due_in_hours=24)
        closed = await self.make_case("counsellor1", state="closed", due_in_hours=-9)
        self.assertEqual(await self.scan(), (1, 0))
        self.assertEqual(await self.scan(), (0, 0))  # idempotent per (case, deadline_version, level)
        c = await self.get_case(overdue)
        self.assertEqual((c.version, c.escalation_level, c.escalated_deadline_version), (2, 1, c.deadline_version))
        for cid in (future, closed):
            self.assertEqual((await self.get_case(cid)).version, 1)
        async with self.sessionmaker() as s:
            ev = (await s.execute(select(CaseEvent).where(CaseEvent.event_type == "CASE_ESCALATED"))).scalars().all()
            self.assertEqual([(e.case_id, e.actor_id) for e in ev], [(overdue, "system-worker")])
            out = await rows(s, NotificationOutbox)
            self.assertEqual({(o.template_key, o.recipient_id) for o in out},
                             {("CASE_ESCALATION_OWNER", self.ids["counsellor1"]), ("CASE_ESCALATION_SUPERVISOR", self.ids["hod"])})
            self.assertTrue(all(o.case_id == overdue for o in out))
            audits = (await s.execute(select(AuditEvent).where(AuditEvent.action == "CASE_ESCALATED"))).scalars().all()
            self.assertEqual(len(audits), 1)
        # the API reports it
        r = await self.client.get(f"/api/v1/cases/{overdue}", headers=self.h("counsellor1"))
        self.assertTrue(r.json()["is_escalated"])
        self.assertTrue(r.json()["is_overdue"])

    async def test_new_due_date_rearms_escalation(self):
        cid = await self.make_case("counsellor1", due_in_hours=-2)
        await self.scan()
        r = await self.client.patch(f"/api/v1/cases/{cid}", headers=self.h("counsellor1"),
                                    json={"expected_version": 2, "due_date": (utc_now() - timedelta(hours=1)).isoformat()})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse((await self.client.get(f"/api/v1/cases/{cid}", headers=self.h("counsellor1"))).json()["is_escalated"])
        self.assertEqual(await self.scan(), (1, 0))
        self.assertEqual((await self.get_case(cid)).escalated_deadline_version, 2)

    async def test_multi_level_chain_follows_campus_settings(self):
        await self.set_levels([{"after_hours": 0, "target": "role:hod"}, {"after_hours": 24, "target": "role:institution_admin"}])
        cid = await self.make_case("counsellor1", due_in_hours=-1)
        self.assertEqual(await self.scan(), (1, 0))                       # level 1 now
        self.assertEqual(await self.scan(), (0, 0))                       # level 2 not due yet
        self.assertEqual(await self.scan(utc_now() + timedelta(hours=24)), (1, 0))
        self.assertEqual(await self.scan(utc_now() + timedelta(hours=48)), (0, 0))
        self.assertEqual((await self.get_case(cid)).escalation_level, 2)
        async with self.sessionmaker() as s:
            sup = {o.recipient_id for o in await rows(s, NotificationOutbox) if o.template_key == "CASE_ESCALATION_SUPERVISOR"}
        self.assertEqual(sup, {self.ids["hod"], self.ids["admin"], self.ids["admin2"]})

    async def test_unresolvable_target_logs_warning_but_still_escalates(self):
        await self.set_levels([{"after_hours": 0, "target": "role:leadership"}])
        cid = await self.make_case("counsellor1", due_in_hours=-1)
        with self.assertLogs("disha.escalation", level="WARNING"):
            self.assertEqual(await self.scan(), (1, 0))
        self.assertEqual((await self.get_case(cid)).escalation_level, 1)

    async def test_campus_contact_is_used_when_role_has_no_members(self):
        await self.set_levels([{"after_hours": 0, "target": "role:leadership"}], contact=self.ids["admin"])
        await self.make_case("counsellor1", due_in_hours=-1)
        await self.scan()
        async with self.sessionmaker() as s:
            sup = [o.recipient_id for o in await rows(s, NotificationOutbox) if o.template_key == "CASE_ESCALATION_SUPERVISOR"]
        self.assertEqual(sup, [self.ids["admin"]])

    async def test_other_campus_cases_use_their_own_chain(self):
        await self.make_case("counsellorB", campus=CAMPUS_B, student=self.ids["studentB"], due_in_hours=-1)
        self.assertEqual(await self.scan(), (1, 0))
        async with self.sessionmaker() as s:
            out = await rows(s, NotificationOutbox)
        self.assertTrue(all(o.campus_id == CAMPUS_B for o in out))
        self.assertEqual({o.template_key for o in out}, {"CASE_ESCALATION_OWNER"})  # campus B has no HOD

    async def test_overdue_followup_escalates_once_and_rearms_on_reschedule(self):
        cid = await self.make_case("counsellor1")
        base = f"/api/v1/cases/{cid}/follow-ups"
        late = (await self.client.post(base, json={"title": "Call", "scheduled_at": (utc_now() - timedelta(hours=3)).isoformat()},
                                       headers=self.h("counsellor1", with_idem=True))).json()["id"]
        await self.client.post(base, json={"title": "Later", "scheduled_at": (utc_now() + timedelta(hours=3)).isoformat()},
                               headers=self.h("counsellor1", with_idem=True))
        self.assertEqual(await self.scan(), (0, 1))
        self.assertEqual(await self.scan(), (0, 0))
        async with self.sessionmaker() as s:
            self.assertIsNotNone((await s.get(FollowUp, late)).escalated_at)
            templates = sorted(o.template_key for o in await rows(s, NotificationOutbox))
        self.assertEqual(templates, ["FOLLOWUP_ESCALATION_SUPERVISOR", "FOLLOWUP_OVERDUE_OWNER"])
        shown = (await self.client.get(base, headers=self.h("counsellor1"))).json()
        self.assertEqual([f["is_escalated"] for f in shown], [True, False])
        # rescheduling to another past time re-arms it
        await self.client.patch(f"{base}/{late}", json={"scheduled_at": (utc_now() - timedelta(hours=1)).isoformat()}, headers=self.h("counsellor1"))
        self.assertEqual(await self.scan(), (0, 1))

    async def test_completed_followup_and_closed_case_followup_are_not_escalated(self):
        cid = await self.make_case("counsellor1")
        base = f"/api/v1/cases/{cid}/follow-ups"
        fid = (await self.client.post(base, json={"title": "Done", "scheduled_at": (utc_now() - timedelta(hours=3)).isoformat()},
                                      headers=self.h("counsellor1", with_idem=True))).json()["id"]
        await self.client.post(f"{base}/{fid}/complete", json={}, headers=self.h("counsellor1"))
        self.assertEqual(await self.scan(), (0, 0))

    async def test_default_chain_uses_env_target_without_campus_row(self):
        async with self.sessionmaker() as s:
            await s.delete(await s.get(Campus, CAMPUS_A))
            await s.commit()
        with patch.object(settings, "DISHA_ESCALATION_TARGET", "role:institution_admin"):
            await self.make_case("counsellor1", due_in_hours=-1)
            await self.scan()
        async with self.sessionmaker() as s:
            sup = {o.recipient_id for o in await rows(s, NotificationOutbox) if o.template_key == "CASE_ESCALATION_SUPERVISOR"}
        self.assertEqual(sup, {self.ids["admin"], self.ids["admin2"]})


if __name__ == "__main__":
    unittest.main()
