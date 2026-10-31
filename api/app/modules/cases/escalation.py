"""Deadline escalation for cases and follow-ups (blueprint 07 section 4). Called by the worker.

* ESC-02  one escalation per (case, deadline_version, level); changing ``due_date`` bumps
          ``deadline_version`` and re-arms it.
* ESC-03/04  the chain comes from campus settings (``escalation_levels``: hours past the deadline and a
          target ``role:<role>`` or ``contact``). Without a campus settings row, one level fires at the
          deadline to ``DISHA_ESCALATION_TARGET``.
* ESC-05  rows are claimed with ``FOR UPDATE SKIP LOCKED`` on PostgreSQL, and every case update is
          conditional on the version read, so two workers cannot escalate the same level twice.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.modules.audit.services import AuditService
from app.modules.campus.models import Campus
from app.modules.campus.schemas import CampusSettings, EscalationLevel
from app.modules.cases.access import TERMINAL_STATES, aware
from app.modules.cases.models import Case, CaseEvent, FollowUp
from app.modules.identity.models import Membership
from app.modules.notifications.services import NotificationOutboxService
from app.shared.enums import map_status_to_state
from app.shared.utils import utc_now

logger = logging.getLogger("disha.escalation")

SYSTEM_ACTOR = "system-worker"


def _default_settings() -> CampusSettings:
    """Used when a campus has no settings row: one level at the deadline, to the env-configured target."""
    target = app_settings.DISHA_ESCALATION_TARGET
    try:
        return CampusSettings(escalation_levels=[EscalationLevel(after_hours=0, target=target)])
    except ValueError:
        return CampusSettings()


class _Settings:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: Dict[str, CampusSettings] = {}

    async def get(self, campus_id: str) -> CampusSettings:
        if campus_id not in self._cache:
            raw = (await self.db.execute(select(Campus.settings).where(Campus.id == campus_id))).scalar_one_or_none()
            self._cache[campus_id] = CampusSettings.model_validate(raw) if raw else _default_settings()
        return self._cache[campus_id]


async def _resolve_targets(
    db: AsyncSession, campus_id: str, level: EscalationLevel, cfg: CampusSettings, owner_id: Optional[str]
) -> List[str]:
    """User ids to notify for a level, never including the owner."""
    ids: List[str] = []
    if level.target.startswith("role:"):
        role = level.target.split(":", 1)[1]
        members = list((await db.execute(
            select(Membership).where(
                Membership.campus_id == campus_id, Membership.role == role, Membership.is_active == True  # noqa: E712
            )
        )).scalars().all())
        if role == "hod" and owner_id:
            owner_mem = (await db.execute(
                select(Membership).where(Membership.user_id == owner_id, Membership.campus_id == campus_id,
                                         Membership.is_active == True)  # noqa: E712
            )).scalars().first()
            if owner_mem and owner_mem.department:
                same = [m for m in members if m.department == owner_mem.department]
                members = same or members  # the owner's own HOD, else any HOD
        ids = [m.user_id for m in members]
    if not ids and cfg.escalation_contact_user_id:
        ok = (await db.execute(
            select(Membership.id).where(
                Membership.user_id == cfg.escalation_contact_user_id, Membership.campus_id == campus_id,
                Membership.is_active == True,  # noqa: E712
            ).limit(1)
        )).first()
        if ok:
            ids = [cfg.escalation_contact_user_id]
    return [i for i in dict.fromkeys(ids) if i != owner_id]


def _claim(stmt, db: AsyncSession):
    dialect = getattr(getattr(db, "bind", None), "dialect", None)
    if dialect is not None and dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    return stmt


async def escalate_overdue_cases(db: AsyncSession, now: datetime, batch_size: int = 100) -> int:
    cfgs = _Settings(db)
    stmt = _claim(
        select(Case).where(
            Case.status.notin_(TERMINAL_STATES), Case.due_date.is_not(None), Case.due_date < now
        ).order_by(Case.due_date).limit(batch_size),
        db,
    )
    escalated = 0
    for case in list((await db.execute(stmt)).scalars().all()):
        cfg = await cfgs.get(case.campus_id)
        current = case.escalation_level if case.escalated_deadline_version == case.deadline_version else 0
        if current >= len(cfg.escalation_levels):
            continue
        level = cfg.escalation_levels[current]
        if aware(case.due_date) + timedelta(hours=level.after_hours) > now:
            continue
        level_no = current + 1
        state = map_status_to_state(case.status).value
        dv, old_version = case.deadline_version, case.version
        async with db.begin_nested():
            res = await db.execute(
                update(Case).where(
                    Case.id == case.id, Case.campus_id == case.campus_id, Case.version == old_version,
                    Case.deadline_version == dv, Case.escalation_level == case.escalation_level,
                ).values(
                    escalated_deadline_version=dv, escalation_level=level_no, escalated_at=now,
                    version=Case.version + 1, updated_at=now,
                )
            )
            if res.rowcount == 0:
                continue  # another worker or a user got there first
            db.add(CaseEvent(
                case_id=case.id, actor_id=SYSTEM_ACTOR, campus_id=case.campus_id, event_type="CASE_ESCALATED",
                payload={"from_state": state, "to_state": state,
                         "metadata": {"level": level_no, "deadline_version": dv, "actor_kind": "system_worker",
                                      "version": old_version + 1}},
                created_at=now,
            ))
            targets = await _resolve_targets(db, case.campus_id, level, cfg, case.assigned_counsellor_id)
            await AuditService.record_event(
                db, actor_id=SYSTEM_ACTOR, campus_id=case.campus_id, entity_type="case", entity_id=case.id,
                action="CASE_ESCALATED",
                event_metadata={"level": level_no, "deadline_version": dv, "recipients": len(targets)},
            )
            payload = {"case_id": case.id, "level": level_no}
            base = f"case-{case.id}-dv{dv}-lvl{level_no}"
            if case.assigned_counsellor_id:
                await NotificationOutboxService.enqueue(
                    db, campus_id=case.campus_id, recipient_id=case.assigned_counsellor_id,
                    template_key="CASE_ESCALATION_OWNER", safe_payload=payload,
                    idempotency_key=f"{base}-owner", case_id=case.id,
                )
            for uid in targets:
                await NotificationOutboxService.enqueue(
                    db, campus_id=case.campus_id, recipient_id=uid, template_key="CASE_ESCALATION_SUPERVISOR",
                    safe_payload=payload, idempotency_key=f"{base}-{uid}", case_id=case.id,
                )
            if not targets:
                logger.warning(
                    "Case %s escalated to level %d but no supervisor could be resolved for target '%s' "
                    "(configure campus escalation_levels or escalation_contact_user_id)",
                    case.id, level_no, level.target,
                )
        escalated += 1
    return escalated


async def escalate_overdue_followups(db: AsyncSession, now: datetime, batch_size: int = 100) -> int:
    cfgs = _Settings(db)
    stmt = _claim(
        select(FollowUp, Case).join(Case, Case.id == FollowUp.case_id).where(
            FollowUp.status == "scheduled", FollowUp.escalated_at.is_(None), FollowUp.scheduled_at < now,
            Case.status.notin_(TERMINAL_STATES),
        ).order_by(FollowUp.scheduled_at).limit(batch_size),
        db,
    )
    escalated = 0
    for fu, case in list((await db.execute(stmt)).all()):
        cfg = await cfgs.get(fu.campus_id)
        if aware(fu.scheduled_at) + timedelta(hours=cfg.followup_grace_hours) > now:
            continue
        scheduled_ts = int(aware(fu.scheduled_at).timestamp())
        async with db.begin_nested():
            res = await db.execute(
                update(FollowUp).where(
                    FollowUp.id == fu.id, FollowUp.status == "scheduled", FollowUp.escalated_at.is_(None)
                ).values(escalated_at=now, updated_at=now)
            )
            if res.rowcount == 0:
                continue
            targets = await _resolve_targets(db, fu.campus_id, cfg.escalation_levels[0], cfg, fu.counsellor_id)
            await AuditService.record_event(
                db, actor_id=SYSTEM_ACTOR, campus_id=fu.campus_id, entity_type="follow_up", entity_id=fu.id,
                action="FOLLOWUP_ESCALATED", event_metadata={"case_id": fu.case_id, "recipients": len(targets)},
            )
            payload = {"case_id": fu.case_id, "followup_id": fu.id}
            base = f"followup-{fu.id}-{scheduled_ts}"
            await NotificationOutboxService.enqueue(
                db, campus_id=fu.campus_id, recipient_id=fu.counsellor_id, template_key="FOLLOWUP_OVERDUE_OWNER",
                safe_payload=payload, idempotency_key=f"{base}-owner", case_id=fu.case_id,
            )
            for uid in targets:
                await NotificationOutboxService.enqueue(
                    db, campus_id=fu.campus_id, recipient_id=uid, template_key="FOLLOWUP_ESCALATION_SUPERVISOR",
                    safe_payload=payload, idempotency_key=f"{base}-{uid}", case_id=fu.case_id,
                )
        escalated += 1
    return escalated


async def scan_and_escalate(db: AsyncSession, now: Optional[datetime] = None) -> Tuple[int, int]:
    """Escalate overdue cases and follow-ups. Commits. Returns (cases, follow_ups) escalated."""
    now = now or utc_now()
    cases = await escalate_overdue_cases(db, now)
    followups = await escalate_overdue_followups(db, now)
    await db.commit()
    return cases, followups
