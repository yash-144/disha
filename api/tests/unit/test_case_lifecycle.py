"""Case lifecycle, audit trail, campus membership, outbox, escalation. SQLite stands in for Postgres."""
import asyncio
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.exceptions import DishaBaseException
from app.main import app
from app.modules.campus.models import CampusMembership
from app.modules.cases.models import Case, CaseEvent, CaseTask, OutboxItem
from app.modules.cases.outbox import dispatch_batch
from app.modules.cases.services import CasesService, TRANSITIONS, escalate_overdue
from app.shared.utils import utc_now
from .conftest import CAMPUS, USER, headers


def run(sm, fn):
    async def go():
        async with sm() as db:
            return await fn(db)
    return asyncio.run(go())


def new_case(sm, flag="f1"):
    return run(sm, lambda db: CasesService(db).create_from_flag(CAMPUS, USER, flag, "S1", "mentor_call", ["B", "a"], "HIGH"))


def walk(sm, case_id, *states):
    """Drive a case through states (assign handles the due_at/owner guard)."""
    async def go(db):
        svc = CasesService(db)
        for st in states:
            c = await svc.repo.get(CAMPUS, case_id)
            if st == "assigned":
                await svc.assign(CAMPUS, case_id, USER, USER, utc_now() + timedelta(days=2), c.version)
            else:
                await svc.transition(CAMPUS, case_id, USER, ["mentor"], st, c.version)
    run(sm, go)


def events(sm, case_id):
    async def go(db):
        return [e.event_type for e in await CasesService(db).repo.events(CAMPUS, case_id)]
    return run(sm, go)


def test_create_is_idempotent_and_writes_event_and_outbox(sm):
    a, b = new_case(sm), new_case(sm)
    assert a.id == b.id and a.state == "action_planned"
    assert events(sm, a.id) == ["CASE_CREATED_FROM_SIGNAL"]
    rows = run(sm, lambda db: db.execute(select(OutboxItem)))
    assert len(rows.scalars().all()) == 1


def test_happy_path_writes_one_event_per_transition(sm):
    c = new_case(sm)
    walk(sm, c.id, "assigned", "accepted", "contact_attempted", "support_in_progress", "follow_up_due")
    assert events(sm, c.id) == ["CASE_CREATED_FROM_SIGNAL", "OWNER_ASSIGNED", "ASSIGNMENT_ACCEPTED", "CONTACT_ATTEMPTED",
                                "SUPPORT_STARTED", "SUPPORT_DELIVERED"]


def test_illegal_transition_is_rejected_and_not_audited(sm):
    c = new_case(sm)
    with pytest.raises(DishaBaseException) as e:
        walk(sm, c.id, "closed")
    assert e.value.status_code == 409
    assert events(sm, c.id) == ["CASE_CREATED_FROM_SIGNAL"]
    assert ("action_planned", "closed") not in TRANSITIONS


def test_stale_version_conflicts(sm):
    c = new_case(sm)
    with pytest.raises(DishaBaseException) as e:
        run(sm, lambda db: CasesService(db).assign(CAMPUS, c.id, USER, "u2", utc_now(), version=99))
    assert e.value.status_code == 409


def test_only_owner_accepts_and_assign_is_required_for_assigned(sm):
    c = new_case(sm)
    with pytest.raises(DishaBaseException) as e:
        run(sm, lambda db: CasesService(db).transition(CAMPUS, c.id, USER, ["mentor"], "assigned", 1))
    assert e.value.status_code == 422
    run(sm, lambda db: CasesService(db).assign(CAMPUS, c.id, USER, "owner-2", utc_now() + timedelta(days=1), 1))
    with pytest.raises(DishaBaseException) as e:
        run(sm, lambda db: CasesService(db).transition(CAMPUS, c.id, USER, ["mentor"], "accepted", 2))
    assert e.value.status_code == 403


def test_events_are_append_only(sm):
    c = new_case(sm)

    async def tamper(db):
        ev = (await db.execute(select(CaseEvent))).scalars().first()
        ev.reason_code = "X"
        await db.commit()
    with pytest.raises(ValueError):
        run(sm, tamper)

    async def delete(db):
        await db.delete((await db.execute(select(CaseEvent))).scalars().first())
        await db.commit()
    with pytest.raises(ValueError):
        run(sm, delete)


def test_outcome_persisted_once_per_cycle_and_counted(sm):
    c = new_case(sm)
    walk(sm, c.id, "assigned", "accepted", "contact_attempted", "support_in_progress", "follow_up_due")
    svc = lambda db: CasesService(db).record_outcome(CAMPUS, c.id, USER, "improved", "mentor_call", ["b", "A"], "HIGH")
    run(sm, svc)
    with pytest.raises(DishaBaseException):
        run(sm, svc)  # second outcome in the same cycle
    case = run(sm, lambda db: CasesService(db).repo.get(CAMPUS, c.id))
    assert case.state == "outcome_reviewed"
    walk(sm, c.id, "closed")
    stats = run(sm, lambda db: CasesService(db).repo.outcome_counts(CAMPUS))
    assert stats == [{"intervention_id": "mentor_call", "reason_pattern": "A+B", "improved": 1, "no_change": 0,
                      "worse": 0, "total": 1}]
    assert run(sm, lambda db: CasesService(db).repo.outcome_counts("other-campus")) == []


def test_closing_from_outcome_reviewed_needs_outcome(sm):
    c = new_case(sm)
    walk(sm, c.id, "assigned", "accepted", "contact_attempted", "support_in_progress", "follow_up_due")
    with pytest.raises(DishaBaseException):
        walk(sm, c.id, "outcome_reviewed")  # no outcome row yet


def test_reopen_starts_new_cycle(sm):
    c = new_case(sm)
    walk(sm, c.id, "assigned", "accepted", "contact_attempted", "failed_contact", "closed", "reopened")
    assert run(sm, lambda db: CasesService(db).repo.get(CAMPUS, c.id)).cycle == 2


# ---- campus membership ----
def test_membership_403_for_foreign_campus_and_non_member():
    with TestClient(app) as client:
        assert client.get("/api/v1/cases/", headers=headers()).status_code == 200
        assert client.get("/api/v1/cases/", headers=headers(campus="other")).status_code == 403
        assert client.get("/api/v1/cases/", headers=headers(sub="stranger")).status_code == 403
        assert client.get("/api/v1/meko/tools", headers=headers(campus="other")).status_code == 403
        no_campus = {k: v for k, v in headers().items() if k != "X-Campus-ID"}
        assert client.get("/api/v1/cases/", headers=no_campus).status_code == 400


def test_inactive_membership_is_rejected(sm):
    async def deactivate(db):
        m = (await db.execute(select(CampusMembership))).scalars().first()
        m.is_active = False
        await db.commit()
    run(sm, deactivate)
    with TestClient(app) as client:
        assert client.get("/api/v1/cases/", headers=headers()).status_code == 403


def test_api_flow_create_assign_transition_and_detail():
    with TestClient(app) as client:
        r = client.post("/api/v1/cases/flags/review", headers=headers(), json={
            "flag_id": "f9", "student_id": "S9", "action": "open_case", "reason_codes": ["LOW_ATTENDANCE"]})
        cid = r.json()["case_id"]
        assert cid
        due = (utc_now() + timedelta(days=2)).isoformat()
        assert client.post(f"/api/v1/cases/{cid}/assign", headers=headers(), json={
            "owner_id": USER, "due_at": due, "version": 1}).json()["state"] == "assigned"
        bad = client.post(f"/api/v1/cases/{cid}/transition", headers=headers(), json={"to_state": "closed", "version": 2})
        assert bad.status_code == 409
        ok = client.post(f"/api/v1/cases/{cid}/transition", headers=headers(), json={"to_state": "accepted", "version": 2})
        assert ok.json()["version"] == 3
        d = client.get(f"/api/v1/cases/{cid}", headers=headers()).json()
        assert [e["event_type"] for e in d["events"]] == ["CASE_CREATED_FROM_SIGNAL", "OWNER_ASSIGNED", "ASSIGNMENT_ACCEPTED"]
        assert client.get(f"/api/v1/cases/{uuid.uuid4()}", headers=headers()).status_code == 404
        # another campus's member cannot see it even if they know the id
        assert client.get(f"/api/v1/cases/{cid}", headers=headers(campus="other")).status_code == 403


def test_restricted_details_only_for_restricted_domains(sm):
    c = new_case(sm)
    run(sm, lambda db: CasesService(db).add_task(CAMPUS, c.id, USER, "finance", "Fee plan", restricted={"amount": 5}))
    with pytest.raises(DishaBaseException):
        run(sm, lambda db: CasesService(db).add_task(CAMPUS, c.id, USER, "academic", "x", restricted={"a": 1}))


# ---- outbox ----
def add_item(sm, **kw):
    async def go(db):
        item = OutboxItem(campus_id=CAMPUS, template_key="T", idempotency_key=str(uuid.uuid4()), **kw)
        db.add(item)
        await db.commit()
        return item.id
    return run(sm, go)


def item(sm, iid):
    return run(sm, lambda db: db.get(OutboxItem, iid))


def test_outbox_retries_with_exponential_backoff_then_dead_letters(sm):
    iid = add_item(sm)
    calls = []

    async def boom(it):
        calls.append(1)
        raise RuntimeError("smtp down")
    t0 = utc_now()
    for attempt in (1, 2, 3):  # backoff 5s, 10s, 20s
        stats = run(sm, lambda db: dispatch_batch(db, {"in_app": boom}, now=t0 + timedelta(hours=attempt), max_attempts=4, base_backoff=5))
        assert stats["retry"] == 1
        it = item(sm, iid)
        assert it.attempts == attempt and it.status == "pending"
        gap = (it.next_attempt_at.replace(tzinfo=None) - (t0 + timedelta(hours=attempt)).replace(tzinfo=None)).total_seconds()
        assert gap == 5 * 2 ** (attempt - 1)
    # not due yet -> untouched
    assert run(sm, lambda db: dispatch_batch(db, {"in_app": boom}, now=t0 + timedelta(hours=3, seconds=1), max_attempts=4)) == {"sent": 0, "retry": 0, "dead_letter": 0}
    stats = run(sm, lambda db: dispatch_batch(db, {"in_app": boom}, now=t0 + timedelta(hours=9), max_attempts=4))
    assert stats["dead_letter"] == 1 and len(calls) == 4
    it = item(sm, iid)
    assert it.status == "dead_letter" and "smtp down" in it.last_error
    # dead letters are never picked up again
    assert run(sm, lambda db: dispatch_batch(db, {"in_app": boom}, now=t0 + timedelta(days=9)))["retry"] == 0


def test_outbox_sends_and_handles_unknown_or_missing_adapters(sm):
    ok, unknown = add_item(sm), add_item(sm, adapter_key="carrier_pigeon")

    async def fine(it):
        pass
    assert run(sm, lambda db: dispatch_batch(db, {}))["sent"] == 0  # no adapters: stays pending
    assert item(sm, ok).status == "pending"
    stats = run(sm, lambda db: dispatch_batch(db, {"in_app": fine}))
    assert stats == {"sent": 1, "retry": 0, "dead_letter": 1}
    assert item(sm, ok).status == "sent" and item(sm, ok).sent_at
    assert item(sm, unknown).status == "dead_letter" and item(sm, unknown).last_error == "UNKNOWN_ADAPTER"


# ---- escalation ----
def test_escalation_of_overdue_case_and_task_is_audited_and_idempotent(sm):
    c = new_case(sm)
    past = utc_now() - timedelta(hours=1)
    run(sm, lambda db: CasesService(db).assign(CAMPUS, c.id, USER, USER, past, 1))
    t = run(sm, lambda db: CasesService(db).add_task(CAMPUS, c.id, USER, "academic", "Call", due_at=past))
    fresh = new_case(sm, "f2")  # no deadline -> never escalated

    assert run(sm, lambda db: escalate_overdue(db)) == {"cases": 1, "tasks": 1}
    assert run(sm, lambda db: escalate_overdue(db)) == {"cases": 0, "tasks": 0}  # idempotent

    case = run(sm, lambda db: CasesService(db).repo.get(CAMPUS, c.id))
    assert case.is_escalated and case.version == 3
    assert set(events(sm, c.id)[-2:]) == {"TASK_ESCALATED", "CASE_ESCALATED"}
    esc = run(sm, lambda db: db.execute(select(CaseEvent).where(CaseEvent.event_type == "CASE_ESCALATED")))
    assert esc.scalars().one().actor_kind == "system_worker"
    out = run(sm, lambda db: db.execute(select(OutboxItem.template_key).where(OutboxItem.template_key.like("%ESCALATION%"))))
    assert sorted(out.scalars()) == ["CASE_ESCALATION_SUPERVISOR", "TASK_ESCALATION_SUPERVISOR"]
    assert run(sm, lambda db: db.get(CaseTask, t.id)).is_escalated
    assert not run(sm, lambda db: db.get(Case, fresh.id)).is_escalated

    # a new due_at re-arms escalation (ESC-02)
    run(sm, lambda db: CasesService(db).assign(CAMPUS, c.id, USER, USER, past, 3))
    assert run(sm, lambda db: escalate_overdue(db))["cases"] == 1


def test_closed_cases_are_not_escalated(sm):
    c = new_case(sm)
    walk(sm, c.id, "assigned")
    async def backdate(db):
        case = await db.get(Case, c.id)
        case.due_at, case.state = utc_now() - timedelta(days=1), "closed"
        await db.commit()
    run(sm, backdate)
    assert run(sm, lambda db: escalate_overdue(db)) == {"cases": 0, "tasks": 0}
