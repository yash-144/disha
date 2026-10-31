"""Interventions, outcomes and follow-ups attached to cases.

State changes of the case itself stay in ``CaseService`` (14-state machine). This module records the
facts the machine's guards depend on: a completed ``support_delivered`` follow-up lets a case move to
``follow_up_due``, and an outcome row lets it move to ``outcome_reviewed``. Services flush and audit;
routes commit.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TenancyContext
from app.core.exceptions import DishaBaseException, EntityNotFoundError, PermissionDeniedError, StateTransitionError
from app.core.permissions import Role
from app.modules.audit.services import AuditService
from app.modules.cases.access import (
    TERMINAL_STATES,
    aware,
    assert_case_open,
    assert_case_writer,
    load_case,
)
from app.modules.cases.models import (
    Case,
    FollowUp,
    FollowUpNote,
    Intervention,
    InterventionCatalogue,
    InterventionOutcome,
)
from app.modules.interventions.schemas import (
    CatalogueCreate,
    CatalogueUpdate,
    FollowUpCancel,
    FollowUpComplete,
    FollowUpCreate,
    FollowUpNoteCreate,
    FollowUpNoteOut,
    FollowUpOut,
    FollowUpReschedule,
    InterventionCreate,
    InterventionOut,
    InterventionProgressUpdate,
    OutcomeCreate,
    OutcomeOut,
)
from app.shared.enums import CaseState, map_status_to_state
from app.shared.utils import utc_now

_PROGRESS_TRANSITIONS = {
    "not_started": {"in_progress", "cancelled", "completed"},
    "in_progress": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
# an intervention only makes sense once a plan exists
_NO_INTERVENTION_STATES = {CaseState.SUGGESTED.value, CaseState.UNDER_REVIEW.value, *TERMINAL_STATES}


def _can_read(ctx: TenancyContext, case: Case) -> None:
    """Owner, HOD, platform admin, or (read-only) institution admin."""
    if ctx.role == Role.INSTITUTION_ADMIN:
        return
    assert_case_writer(ctx, case)


class CatalogueService:
    @staticmethod
    async def list(db: AsyncSession, campus_id: str, include_inactive: bool) -> List[InterventionCatalogue]:
        stmt = select(InterventionCatalogue).where(
            (InterventionCatalogue.campus_id == campus_id) | (InterventionCatalogue.campus_id.is_(None))
        )
        if not include_inactive:
            stmt = stmt.where(InterventionCatalogue.is_active == True)  # noqa: E712
        return list((await db.execute(stmt.order_by(InterventionCatalogue.name))).scalars().all())

    @staticmethod
    async def _name_taken(db, campus_id, name, exclude_id=None) -> bool:
        stmt = select(InterventionCatalogue.id).where(
            InterventionCatalogue.campus_id == campus_id, InterventionCatalogue.name == name
        )
        if exclude_id:
            stmt = stmt.where(InterventionCatalogue.id != exclude_id)
        return (await db.execute(stmt)).first() is not None

    @staticmethod
    async def create(db: AsyncSession, ctx: TenancyContext, data: CatalogueCreate) -> InterventionCatalogue:
        name = data.name.strip()
        if await CatalogueService._name_taken(db, ctx.campus_id, name):
            raise DishaBaseException("An intervention with this name already exists on the campus", 409)
        item = InterventionCatalogue(
            campus_id=ctx.campus_id, name=name, description=data.description, category=data.category, is_active=True
        )
        db.add(item)
        await db.flush()
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="intervention_catalogue",
            entity_id=item.id, action="CATALOGUE_ITEM_CREATED", event_metadata={"name": name},
        )
        return item

    @staticmethod
    async def update(db: AsyncSession, ctx: TenancyContext, item_id: str, data: CatalogueUpdate) -> InterventionCatalogue:
        res = await db.execute(select(InterventionCatalogue).where(InterventionCatalogue.id == item_id))
        item = res.scalar_one_or_none()
        # platform-wide entries (campus_id NULL) are not editable from a campus
        if not item or item.campus_id != ctx.campus_id:
            raise EntityNotFoundError("InterventionCatalogue", item_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"]:
            changes["name"] = changes["name"].strip()
            if await CatalogueService._name_taken(db, ctx.campus_id, changes["name"], exclude_id=item.id):
                raise DishaBaseException("An intervention with this name already exists on the campus", 409)
        for k, v in changes.items():
            setattr(item, k, v)
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="intervention_catalogue",
            entity_id=item.id, action="CATALOGUE_ITEM_UPDATED", event_metadata={"fields": sorted(changes)},
        )
        await db.flush()
        return item


def _intervention_out(i: Intervention) -> InterventionOut:
    cat = i.catalogue_entry
    return InterventionOut(
        id=i.id, case_id=i.case_id, catalogue_id=i.catalogue_id, name=cat.name if cat else "",
        category=cat.category if cat else None, counsellor_id=i.counsellor_id, description=i.description,
        start_date=i.start_date, target_date=i.target_date, progress=i.progress,
        outcome=OutcomeOut.model_validate(i.outcome) if i.outcome else None,
        created_at=i.created_at, updated_at=i.updated_at,
    )


class InterventionService:
    @staticmethod
    async def list_for_case(db: AsyncSession, ctx: TenancyContext, case_id: str) -> List[InterventionOut]:
        case = await load_case(db, ctx.campus_id, case_id)
        _can_read(ctx, case)
        res = await db.execute(
            select(Intervention).where(Intervention.case_id == case_id, Intervention.campus_id == ctx.campus_id)
            .order_by(Intervention.created_at)
        )
        return [_intervention_out(i) for i in res.scalars().all()]

    @staticmethod
    async def create(db: AsyncSession, ctx: TenancyContext, case_id: str, data: InterventionCreate) -> InterventionOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        state = map_status_to_state(case.status).value
        if state in _NO_INTERVENTION_STATES:
            raise StateTransitionError(state, state, f"Interventions cannot be added while the case is '{state}'")

        cat = (
            await db.execute(select(InterventionCatalogue).where(InterventionCatalogue.id == data.catalogue_id))
        ).scalar_one_or_none()
        if not cat or not cat.is_active or cat.campus_id not in (None, ctx.campus_id):
            raise EntityNotFoundError("InterventionCatalogue", data.catalogue_id)
        if data.start_date and data.target_date and aware(data.target_date) < aware(data.start_date):
            raise DishaBaseException("target_date must not be before start_date", 422)

        dup = await db.execute(
            select(Intervention.id).where(
                Intervention.case_id == case_id, Intervention.catalogue_id == cat.id,
                Intervention.progress.in_(("not_started", "in_progress")),
            )
        )
        if dup.first():
            raise DishaBaseException("This intervention is already active on the case", 409)

        item = Intervention(
            case_id=case_id, catalogue_id=cat.id, campus_id=ctx.campus_id,
            counsellor_id=case.assigned_counsellor_id or ctx.user_id, description=data.description,
            start_date=data.start_date, target_date=data.target_date, progress="not_started",
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="intervention", entity_id=item.id,
            action="INTERVENTION_SELECTED", event_metadata={"case_id": case_id, "catalogue_id": cat.id},
        )
        return _intervention_out(item)

    @staticmethod
    async def update_progress(
        db: AsyncSession, ctx: TenancyContext, case_id: str, intervention_id: str, data: InterventionProgressUpdate
    ) -> InterventionOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        res = await db.execute(
            select(Intervention).where(
                Intervention.id == intervention_id, Intervention.case_id == case_id,
                Intervention.campus_id == ctx.campus_id,
            )
        )
        item = res.scalar_one_or_none()
        if not item:
            raise EntityNotFoundError("Intervention", intervention_id)
        if data.progress not in _PROGRESS_TRANSITIONS[item.progress]:
            raise StateTransitionError(item.progress, data.progress, "Intervention progress cannot move that way")
        before = item.progress
        item.progress = data.progress
        if data.progress == "in_progress" and item.start_date is None:
            item.start_date = utc_now()
        if data.description is not None:
            item.description = data.description
        if data.target_date is not None:
            item.target_date = data.target_date
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="intervention", entity_id=item.id,
            action="INTERVENTION_PROGRESS_CHANGED", event_metadata={"case_id": case_id, "from": before, "to": data.progress},
        )
        await db.flush()
        await db.refresh(item)
        return _intervention_out(item)

    @staticmethod
    async def record_outcome(db: AsyncSession, ctx: TenancyContext, case_id: str, data: OutcomeCreate) -> OutcomeOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        res = await db.execute(
            select(Intervention).where(
                Intervention.id == data.intervention_id, Intervention.case_id == case_id,
                Intervention.campus_id == ctx.campus_id,
            )
        )
        item = res.scalar_one_or_none()
        if not item:
            raise EntityNotFoundError("Intervention", data.intervention_id)
        if item.progress == "cancelled":
            raise StateTransitionError("cancelled", "completed", "A cancelled intervention cannot have an outcome")
        existing = await db.execute(
            select(InterventionOutcome.id).where(InterventionOutcome.intervention_id == item.id)
        )
        if existing.first():
            raise DishaBaseException("An outcome is already recorded for this intervention", 409)

        outcome = InterventionOutcome(
            case_id=case_id, intervention_id=item.id, counsellor_id=ctx.user_id, campus_id=ctx.campus_id,
            completion_status=data.completion_status, outcome_notes=data.outcome_notes,
            completed_at=data.completed_at or utc_now(),
        )
        db.add(outcome)
        item.progress = "completed"
        await db.flush()
        # no outcome notes in the audit trail
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="intervention_outcome",
            entity_id=outcome.id, action="OUTCOME_RECORDED",
            event_metadata={"case_id": case_id, "intervention_id": item.id, "completion_status": data.completion_status},
        )
        return OutcomeOut.model_validate(outcome)


def _followup_out(fu: FollowUp, include_notes: bool, now: Optional[datetime] = None) -> FollowUpOut:
    now = now or utc_now()
    return FollowUpOut(
        id=fu.id, case_id=fu.case_id, counsellor_id=fu.counsellor_id, title=fu.title, description=fu.description,
        follow_up_type=fu.follow_up_type, contact_status=fu.contact_status, proof_kind=fu.proof_kind,
        scheduled_at=fu.scheduled_at, status=fu.status,
        is_overdue=fu.status == "scheduled" and aware(fu.scheduled_at) < now,
        is_escalated=fu.escalated_at is not None, completed_at=fu.completed_at, completed_by=fu.completed_by,
        notes=[FollowUpNoteOut.model_validate(n) for n in sorted(fu.followup_notes, key=lambda n: n.created_at)]
        if include_notes else [],
        created_at=fu.created_at,
    )


async def _load_followup(db: AsyncSession, ctx: TenancyContext, case_id: str, followup_id: str) -> FollowUp:
    res = await db.execute(
        select(FollowUp).where(
            FollowUp.id == followup_id, FollowUp.case_id == case_id, FollowUp.campus_id == ctx.campus_id
        )
    )
    fu = res.scalar_one_or_none()
    if not fu:
        raise EntityNotFoundError("FollowUp", followup_id)
    return fu


class FollowUpService:
    @staticmethod
    def to_out(fu: FollowUp, ctx: TenancyContext) -> FollowUpOut:
        return _followup_out(fu, include_notes=ctx.role != Role.INSTITUTION_ADMIN)

    @staticmethod
    async def list_for_case(db: AsyncSession, ctx: TenancyContext, case_id: str) -> List[FollowUpOut]:
        case = await load_case(db, ctx.campus_id, case_id)
        _can_read(ctx, case)
        res = await db.execute(
            select(FollowUp).where(FollowUp.case_id == case_id, FollowUp.campus_id == ctx.campus_id)
            .order_by(FollowUp.scheduled_at)
        )
        return [FollowUpService.to_out(f, ctx) for f in res.scalars().all()]

    @staticmethod
    async def create(db: AsyncSession, ctx: TenancyContext, case_id: str, data: FollowUpCreate) -> FollowUpOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        assert_case_open(case)
        fu = FollowUp(
            case_id=case_id, campus_id=ctx.campus_id, counsellor_id=case.assigned_counsellor_id or ctx.user_id,
            title=data.title, description=data.description, scheduled_at=data.scheduled_at, status="scheduled",
            follow_up_type=data.follow_up_type, proof_kind=data.proof_kind,
        )
        db.add(fu)
        await db.flush()
        await db.refresh(fu)
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="follow_up", entity_id=fu.id,
            action="FOLLOWUP_SCHEDULED",
            event_metadata={"case_id": case_id, "follow_up_type": data.follow_up_type,
                            "scheduled_at": aware(data.scheduled_at).isoformat()},
        )
        return FollowUpService.to_out(fu, ctx)

    @staticmethod
    async def reschedule(
        db: AsyncSession, ctx: TenancyContext, case_id: str, followup_id: str, data: FollowUpReschedule
    ) -> FollowUpOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        fu = await _load_followup(db, ctx, case_id, followup_id)
        if fu.status != "scheduled":
            raise StateTransitionError(fu.status, "scheduled", "Only scheduled follow-ups can be rescheduled")
        fu.scheduled_at = data.scheduled_at
        fu.escalated_at = None  # re-arms escalation
        if data.title:
            fu.title = data.title
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="follow_up", entity_id=fu.id,
            action="FOLLOWUP_RESCHEDULED",
            event_metadata={"case_id": case_id, "scheduled_at": aware(data.scheduled_at).isoformat()},
        )
        await db.flush()
        return FollowUpService.to_out(fu, ctx)

    @staticmethod
    async def complete(
        db: AsyncSession, ctx: TenancyContext, case_id: str, followup_id: str, data: FollowUpComplete
    ) -> FollowUpOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        fu = await _load_followup(db, ctx, case_id, followup_id)
        if fu.status == "completed":
            return FollowUpService.to_out(fu, ctx)  # idempotent
        if fu.status != "scheduled":
            raise StateTransitionError(fu.status, "completed", "Only scheduled follow-ups can be completed")
        now = utc_now()
        fu.status = "completed"
        fu.completed_at = now
        fu.completed_by = ctx.user_id
        if data.contact_status:
            fu.contact_status = data.contact_status
        if data.proof_kind:
            fu.proof_kind = data.proof_kind
        if data.completion_notes:
            db.add(FollowUpNote(
                followup_id=fu.id, case_id=case_id, author_id=ctx.user_id, campus_id=ctx.campus_id,
                content=data.completion_notes,
            ))
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="follow_up", entity_id=fu.id,
            action="FOLLOWUP_COMPLETED",
            event_metadata={"case_id": case_id, "follow_up_type": fu.follow_up_type, "contact_status": fu.contact_status},
        )
        await db.flush()
        await db.refresh(fu)
        return FollowUpService.to_out(fu, ctx)

    @staticmethod
    async def cancel(
        db: AsyncSession, ctx: TenancyContext, case_id: str, followup_id: str, data: FollowUpCancel
    ) -> FollowUpOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        fu = await _load_followup(db, ctx, case_id, followup_id)
        if fu.status != "scheduled":
            raise StateTransitionError(fu.status, "cancelled", "Only scheduled follow-ups can be cancelled")
        fu.status = "cancelled"
        db.add(FollowUpNote(
            followup_id=fu.id, case_id=case_id, author_id=ctx.user_id, campus_id=ctx.campus_id,
            content=f"Cancelled: {data.reason}",
        ))
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="follow_up", entity_id=fu.id,
            action="FOLLOWUP_CANCELLED", event_metadata={"case_id": case_id},
        )
        await db.flush()
        await db.refresh(fu)
        return FollowUpService.to_out(fu, ctx)

    @staticmethod
    async def add_note(
        db: AsyncSession, ctx: TenancyContext, case_id: str, followup_id: str, data: FollowUpNoteCreate
    ) -> FollowUpOut:
        case = await load_case(db, ctx.campus_id, case_id)
        assert_case_writer(ctx, case)
        fu = await _load_followup(db, ctx, case_id, followup_id)
        db.add(FollowUpNote(
            followup_id=fu.id, case_id=case_id, author_id=ctx.user_id, campus_id=ctx.campus_id, content=data.content,
        ))
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="follow_up", entity_id=fu.id,
            action="FOLLOWUP_NOTE_ADDED", event_metadata={"case_id": case_id},
        )
        await db.flush()
        await db.refresh(fu)
        return FollowUpService.to_out(fu, ctx)
