"""Case lifecycle (blueprint 07): the transition table is data, every change writes a case_event and an
outbox row in the same transaction, and the version check is part of the UPDATE (CASE-SM-04)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import DishaBaseException, EntityNotFoundError, PermissionDeniedError
from app.modules.cases.models import Case, CaseEvent, CaseOutcome, CaseTask, OutboxItem, RestrictedTaskDetail
from app.modules.cases.repository import CaseRepository
from app.shared.utils import utc_now

# (from, to) -> event type. The only place transitions are defined (CASE-SM-01).
TRANSITIONS = {
    ("suggested", "under_review"): "CASE_REVIEW_STARTED",
    ("under_review", "action_planned"): "INTERVENTION_APPROVED",
    ("under_review", "dismissed"): "SIGNAL_DISMISSED",
    ("action_planned", "assigned"): "OWNER_ASSIGNED",
    ("assigned", "assigned"): "OWNER_REASSIGNED",
    ("assigned", "accepted"): "ASSIGNMENT_ACCEPTED",
    ("accepted", "contact_attempted"): "CONTACT_ATTEMPTED",
    ("contact_attempted", "support_in_progress"): "SUPPORT_STARTED",
    ("contact_attempted", "failed_contact"): "CONTACT_FAILED",
    ("support_in_progress", "follow_up_due"): "SUPPORT_DELIVERED",
    ("support_in_progress", "service_unavailable"): "SERVICE_UNAVAILABLE",
    ("follow_up_due", "outcome_reviewed"): "OUTCOME_RECORDED",
    ("outcome_reviewed", "closed"): "CASE_CLOSED",
    ("failed_contact", "closed"): "CASE_CLOSED",
    ("service_unavailable", "closed"): "CASE_CLOSED",
    ("closed", "reopened"): "CASE_REOPENED",
    ("reopened", "assigned"): "OWNER_ASSIGNED",
    ("reopened", "action_planned"): "INTERVENTION_APPROVED",
}
TASK_TRANSITIONS = {
    "pending": {"accepted", "cancelled"}, "accepted": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"}, "completed": set(), "cancelled": set(),
}
RESTRICTED_DOMAINS = {"finance", "counselling"}


def allowed_targets(state: str) -> List[str]:
    return sorted({t for (f, t) in TRANSITIONS if f == state})


def reason_pattern(codes: List[str]) -> str:
    return "+".join(sorted({c.strip().upper() for c in codes if c.strip()}))


def conflict(msg: str) -> DishaBaseException:
    return DishaBaseException(msg, 409)


class CasesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CaseRepository(db)

    async def _case(self, campus_id: str, case_id: str) -> Case:
        case = await self.repo.get(campus_id, case_id)
        if not case:
            raise EntityNotFoundError("Case", case_id)
        return case

    def _outbox(self, case: Case, template: str, key: str, dest: Optional[str] = None, **payload) -> None:
        self.db.add(OutboxItem(campus_id=case.campus_id, case_id=case.id, template_key=template,
                               destination_ref=dest, payload={"case_id": case.id, **payload}, idempotency_key=key))

    async def _change(self, case: Case, *, event_type: str, actor: Optional[str], expected_version: int,
                      to_state: Optional[str] = None, reason: Optional[str] = None, values: Optional[dict] = None,
                      meta: Optional[Dict[str, Any]] = None, template: Optional[str] = None,
                      dest: Optional[str] = None) -> Case:
        """Versioned UPDATE + case_event + outbox row; the caller commits."""
        frm, to = case.state, to_state or case.state
        res = await self.db.execute(
            update(Case).where(Case.id == case.id, Case.campus_id == case.campus_id, Case.version == expected_version)
            .values(state=to, version=Case.version + 1, updated_at=utc_now(), **(values or {}))
            .execution_options(synchronize_session=False))
        if res.rowcount == 0:
            raise conflict("Case was modified by someone else; reload and retry")
        await self.db.refresh(case)
        key = f"{case.id}-v{case.version}"
        self.db.add(CaseEvent(campus_id=case.campus_id, case_id=case.id, actor_id=actor, event_type=event_type,
                              from_state=frm, to_state=to, reason_code=reason, event_metadata=meta or {},
                              idempotency_key=key))
        self._outbox(case, template or f"CASE_STATE_{to.upper()}", f"out-{key}", dest or case.owner_id,
                     from_state=frm, to_state=to)
        return case

    async def create_from_flag(self, campus_id: str, actor: Optional[str], flag_id: str, student_id: str,
                               intervention_id: Optional[str] = None, reason_codes: Optional[List[str]] = None,
                               tier: Optional[str] = None) -> Case:
        """Idempotent per (campus, flag): a second call returns the existing case."""
        if existing := await self.repo.by_flag(campus_id, flag_id):
            return existing
        case = Case(campus_id=campus_id, flag_id=flag_id, student_ref=student_id, intervention_id=intervention_id,
                    reason_codes=reason_codes or [], tier=tier, created_by=actor)
        self.db.add(case)
        try:
            await self.db.flush()
            self.db.add(CaseEvent(campus_id=campus_id, case_id=case.id, actor_id=actor,
                                  event_type="CASE_CREATED_FROM_SIGNAL", from_state=None, to_state=case.state,
                                  event_metadata={"flag_id": flag_id, "intervention_id": intervention_id},
                                  idempotency_key=f"{case.id}-v1"))
            self._outbox(case, "CASE_ACTION_PLANNED", f"out-{case.id}-v1")
            await self.db.commit()
        except IntegrityError:  # lost a race on (campus, flag)
            await self.db.rollback()
            return await self.repo.by_flag(campus_id, flag_id)
        return case

    async def transition(self, campus_id: str, case_id: str, actor: Optional[str], roles: List[str], to_state: str,
                         version: int, reason: Optional[str] = None) -> Case:
        case = await self._case(campus_id, case_id)
        frm = case.state
        event_type = TRANSITIONS.get((frm, to_state))
        if event_type is None:
            raise conflict(f"Transition '{frm}' -> '{to_state}' is not allowed; valid: {allowed_targets(frm)}")
        if to_state == "assigned":
            raise DishaBaseException("Use the assign endpoint: an owner and due_at are required", 422)
        if to_state == "accepted" and actor != case.owner_id and "institution_admin" not in roles:
            raise PermissionDeniedError("Only the assigned owner may accept")
        if to_state == "outcome_reviewed" or frm == "outcome_reviewed":
            if not await self.repo.outcome(case.id, case.cycle):
                raise conflict("An outcome must be recorded first")
        values: Dict[str, Any] = {}
        if to_state == "reopened":  # new outcome cycle, escalation re-armed
            values = {"cycle": Case.cycle + 1, "is_escalated": False}
        try:
            await self._change(case, event_type=event_type, actor=actor, expected_version=version, to_state=to_state,
                               reason=reason, values=values)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return case

    async def assign(self, campus_id: str, case_id: str, actor: Optional[str], owner_id: str, due_at: datetime,
                     version: int, reason: Optional[str] = None) -> Case:
        case = await self._case(campus_id, case_id)
        event_type = TRANSITIONS.get((case.state, "assigned"))
        if event_type is None:
            raise conflict(f"Cannot assign while case is '{case.state}'")
        try:
            await self._change(case, event_type=event_type, actor=actor, expected_version=version,
                               to_state="assigned", reason=reason or "ASSIGNED", dest=owner_id,
                               values={"owner_id": owner_id, "due_at": due_at, "is_escalated": False,
                                       "deadline_version": Case.deadline_version + 1},
                               meta={"owner_id": owner_id, "due_at": due_at.isoformat()},
                               template="CASE_ASSIGNMENT_NOTIFICATION")
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return case

    async def add_task(self, campus_id: str, case_id: str, actor: Optional[str], domain: str, label: str,
                       assignee_id: Optional[str] = None, due_at: Optional[datetime] = None,
                       restricted: Optional[dict] = None) -> CaseTask:
        case = await self._case(campus_id, case_id)
        if restricted and domain not in RESTRICTED_DOMAINS:
            raise DishaBaseException("restricted_details only apply to finance or counselling tasks", 422)
        task = CaseTask(campus_id=campus_id, case_id=case.id, domain=domain, generic_label=label,
                        assignee_id=assignee_id, due_at=due_at)
        self.db.add(task)
        await self.db.flush()
        if restricted:
            self.db.add(RestrictedTaskDetail(campus_id=campus_id, task_id=task.id, details=restricted))
        self.db.add(CaseEvent(campus_id=campus_id, case_id=case.id, actor_id=actor, event_type="TASK_CREATED",
                              from_state=case.state, to_state=case.state, event_metadata={"task_id": task.id},
                              idempotency_key=f"task-{task.id}-new"))
        self._outbox(case, "TASK_ASSIGNED", f"out-task-{task.id}-new", assignee_id, task_id=task.id)
        await self.db.commit()
        return task

    async def set_task_state(self, campus_id: str, task_id: str, actor: Optional[str], to_state: str) -> CaseTask:
        task = await self.repo.task(campus_id, task_id)
        if not task:
            raise EntityNotFoundError("Task", task_id)
        if to_state not in TASK_TRANSITIONS[task.state]:
            raise conflict(f"Task transition '{task.state}' -> '{to_state}' is not allowed")
        frm, task.state = task.state, to_state
        self.db.add(CaseEvent(campus_id=campus_id, case_id=task.case_id, actor_id=actor,
                              event_type=f"TASK_{to_state.upper()}", from_state=frm, to_state=to_state,
                              event_metadata={"task_id": task.id}, idempotency_key=f"task-{task.id}-{to_state}"))
        await self.db.commit()
        return task

    async def record_outcome(self, campus_id: str, case_id: str, actor: Optional[str], outcome: str,
                             intervention_id: str, reason_codes: List[str], tier: Optional[str] = None,
                             checkpoint: Optional[str] = None) -> CaseOutcome:
        """One outcome per case cycle; a case waiting at follow_up_due moves to outcome_reviewed."""
        case = await self._case(campus_id, case_id)
        if await self.repo.outcome(case.id, case.cycle):
            raise conflict("An outcome is already recorded for this case cycle")
        row = CaseOutcome(campus_id=campus_id, case_id=case.id, cycle=case.cycle, outcome=outcome,
                          intervention_id=intervention_id, reason_pattern=reason_pattern(reason_codes), tier=tier,
                          checkpoint=checkpoint, recorded_by=actor)
        self.db.add(row)
        try:
            await self._change(case, event_type="OUTCOME_RECORDED", actor=actor, expected_version=case.version,
                               to_state="outcome_reviewed" if case.state == "follow_up_due" else None,
                               meta={"outcome": outcome, "intervention_id": intervention_id},
                               template="CASE_OUTCOME_RECORDED")
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return row


async def escalate_overdue(db: AsyncSession, now: Optional[datetime] = None) -> Dict[str, int]:
    """Worker scan (ESC-01..06): overdue cases and tasks get a case_event and an outbox notification.

    Idempotency key is (id, deadline_version); assigning a new due_at re-arms the escalation.
    Rows are locked with SKIP LOCKED so parallel workers do not double-escalate.
    """
    now = now or utc_now()
    repo, target = CaseRepository(db), settings.DISHA_ESCALATION_TARGET
    cases, tasks = await repo.overdue_cases(now), await repo.overdue_tasks(now)
    for c in cases:
        key = f"escalate-{c.id}-d{c.deadline_version}"
        c.is_escalated, c.version, c.updated_at = True, c.version + 1, now
        db.add(CaseEvent(campus_id=c.campus_id, case_id=c.id, actor_kind="system_worker", event_type="CASE_ESCALATED",
                         from_state=c.state, to_state=c.state, reason_code="DEADLINE_EXPIRED",
                         event_metadata={"due_at": c.due_at.isoformat(), "target": target}, idempotency_key=key))
        db.add(OutboxItem(campus_id=c.campus_id, case_id=c.id, template_key="CASE_ESCALATION_SUPERVISOR",
                          destination_ref=target, payload={"case_id": c.id}, idempotency_key=f"out-{key}"))
    for t in tasks:
        key = f"escalate-task-{t.id}-d{t.deadline_version}"
        t.is_escalated = True
        db.add(CaseEvent(campus_id=t.campus_id, case_id=t.case_id, actor_kind="system_worker",
                         event_type="TASK_ESCALATED", reason_code="DEADLINE_EXPIRED",
                         event_metadata={"task_id": t.id, "due_at": t.due_at.isoformat(), "target": target},
                         idempotency_key=key))
        db.add(OutboxItem(campus_id=t.campus_id, case_id=t.case_id, template_key="TASK_ESCALATION_SUPERVISOR",
                          destination_ref=target, payload={"case_id": t.case_id, "task_id": t.id},
                          idempotency_key=f"out-{key}"))
    await db.commit()
    return {"cases": len(cases), "tasks": len(tasks)}
