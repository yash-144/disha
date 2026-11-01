"""Counsellor caseload, sessions (appointments), confidential notes and student assignments.

Services flush and audit; routes commit. Everything is filtered by the caller's active campus.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TenancyContext
from app.core.exceptions import DishaBaseException, EntityNotFoundError, PermissionDeniedError, StateTransitionError
from app.core.permissions import Role
from app.modules.audit.services import AuditService
from app.modules.cases.access import TERMINAL_STATES, aware, assert_case_writer, load_case
from app.modules.cases.models import Case, FollowUp
from app.modules.counselling.models import (
    CounsellingNote,
    CounsellingSession,
    CounsellorAssignment,
    CounsellorProfile,
)
from app.modules.counselling.schemas import (
    AssignmentCreate,
    CaseloadItem,
    CounsellorDashboard,
    NoteCreate,
    ProfileUpsert,
    SessionCancel,
    SessionCreate,
    SessionOut,
    SessionReschedule,
    StudentItem,
)
from app.modules.identity.models import Membership
from app.modules.interventions.services import FollowUpService
from app.modules.notifications.models import Notification
from app.modules.notifications.services import NotificationOutboxService
from app.modules.roster.models import Student
from app.shared.enums import map_status_to_state
from app.shared.utils import utc_now

SUPERVISORS = (Role.HOD, Role.PLATFORM_ADMIN)


# ------------------------------------------------------------------ scope
async def student_in_scope(db: AsyncSession, campus_id: str, counsellor_id: str, student_id: str) -> bool:
    """A counsellor may work with a student they are assigned to or who has an open case they own."""
    assigned = await db.execute(
        select(CounsellorAssignment.id).where(
            CounsellorAssignment.campus_id == campus_id, CounsellorAssignment.counsellor_id == counsellor_id,
            CounsellorAssignment.student_id == student_id, CounsellorAssignment.is_active == True,  # noqa: E712
        ).limit(1)
    )
    if assigned.first():
        return True
    owned = await db.execute(
        select(Case.id).where(
            Case.campus_id == campus_id, Case.assigned_counsellor_id == counsellor_id,
            Case.student_id == student_id, Case.status.notin_(TERMINAL_STATES),
        ).limit(1)
    )
    return owned.first() is not None


async def _student(db: AsyncSession, campus_id: str, student_id: str) -> Student:
    res = await db.execute(
        select(Student).where(Student.id == student_id, Student.campus_id == campus_id, Student.is_active == True)  # noqa: E712
    )
    s = res.scalar_one_or_none()
    if not s:
        raise EntityNotFoundError("Student", student_id)
    return s


async def _require_counsellor_member(db: AsyncSession, campus_id: str, user_id: str) -> None:
    res = await db.execute(
        select(Membership.id).where(
            Membership.user_id == user_id, Membership.campus_id == campus_id,
            Membership.role == Role.COUNSELLOR.value, Membership.is_active == True,  # noqa: E712
        )
    )
    if not res.first():
        raise DishaBaseException("That user is not an active counsellor on this campus", 422)


# ---------------------------------------------------------------- profile
class ProfileService:
    @staticmethod
    async def get(db: AsyncSession, ctx: TenancyContext) -> CounsellorProfile:
        res = await db.execute(
            select(CounsellorProfile).where(
                CounsellorProfile.user_id == ctx.user_id, CounsellorProfile.campus_id == ctx.campus_id
            )
        )
        p = res.scalar_one_or_none()
        if not p:
            raise EntityNotFoundError("CounsellorProfile", ctx.user_id)
        return p

    @staticmethod
    async def upsert(db: AsyncSession, ctx: TenancyContext, data: ProfileUpsert) -> CounsellorProfile:
        res = await db.execute(
            select(CounsellorProfile).where(
                CounsellorProfile.user_id == ctx.user_id, CounsellorProfile.campus_id == ctx.campus_id
            )
        )
        p = res.scalar_one_or_none()
        created = p is None
        if created:
            p = CounsellorProfile(user_id=ctx.user_id, campus_id=ctx.campus_id, availability_status="available")
            db.add(p)
        changes = data.model_dump(exclude_unset=True)
        for k, v in changes.items():
            setattr(p, k, v)
        await db.flush()
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counsellor_profile", entity_id=p.id,
            action="PROFILE_CREATED" if created else "PROFILE_UPDATED", event_metadata={"fields": sorted(changes)},
        )
        return p


# ---------------------------------------------------------------- caseload
class CaseloadService:
    @staticmethod
    def _owner(ctx: TenancyContext, counsellor_id: Optional[str]) -> Optional[str]:
        """Counsellors see only their own caseload; supervisors may look at a named counsellor or everyone."""
        if ctx.role == Role.COUNSELLOR:
            if counsellor_id and counsellor_id != ctx.user_id:
                raise PermissionDeniedError("Counsellors can only view their own caseload")
            return ctx.user_id
        return counsellor_id

    @staticmethod
    async def list_cases(
        db: AsyncSession, ctx: TenancyContext, counsellor_id: Optional[str], state: Optional[str],
        overdue_only: bool, include_closed: bool, limit: int, offset: int,
    ) -> List[CaseloadItem]:
        owner = CaseloadService._owner(ctx, counsellor_id)
        stmt = select(Case).where(Case.campus_id == ctx.campus_id)
        if owner:
            stmt = stmt.where(Case.assigned_counsellor_id == owner)
        else:
            stmt = stmt.where(Case.assigned_counsellor_id.is_not(None))
        if state:
            stmt = stmt.where(Case.status == map_status_to_state(state).value)
        elif not include_closed:
            stmt = stmt.where(Case.status.notin_(TERMINAL_STATES))
        stmt = stmt.order_by(Case.due_date.is_(None), Case.due_date, Case.created_at.desc())
        cases = list((await db.execute(stmt)).scalars().all())
        now = utc_now()
        items = []
        for c in cases:
            overdue = bool(c.due_date and aware(c.due_date) < now and c.status not in TERMINAL_STATES)
            if overdue_only and not overdue:
                continue
            items.append(CaseloadItem(
                case_id=c.id, student_id=c.student_id,
                student_name=c.student.full_name if c.student else None,
                student_ref=c.student.student_uid if c.student else None,
                department=c.student.department if c.student else None,
                state=map_status_to_state(c.status).value, priority=c.priority, due_at=c.due_date,
                is_overdue=overdue,
                is_escalated=c.escalated_deadline_version is not None and c.escalated_deadline_version == c.deadline_version,
                version=c.version, updated_at=c.updated_at,
            ))
        return items[offset: offset + limit]

    @staticmethod
    async def list_students(
        db: AsyncSession, ctx: TenancyContext, search: Optional[str], limit: int, offset: int
    ) -> List[StudentItem]:
        if ctx.role != Role.COUNSELLOR:
            raise PermissionDeniedError("Only counsellors have a student caseload")
        assigned = select(CounsellorAssignment.student_id).where(
            CounsellorAssignment.campus_id == ctx.campus_id, CounsellorAssignment.counsellor_id == ctx.user_id,
            CounsellorAssignment.is_active == True,  # noqa: E712
        )
        owned = select(Case.student_id).where(
            Case.campus_id == ctx.campus_id, Case.assigned_counsellor_id == ctx.user_id,
            Case.status.notin_(TERMINAL_STATES),
        )
        stmt = select(Student).where(
            Student.campus_id == ctx.campus_id, Student.is_active == True,  # noqa: E712
            or_(Student.id.in_(assigned), Student.id.in_(owned)),
        )
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(Student.full_name).like(like) | func.lower(Student.student_uid).like(like))
        stmt = stmt.order_by(Student.full_name).limit(limit).offset(offset)
        students = list((await db.execute(stmt)).scalars().all())
        counts = {}
        if students:
            rows = await db.execute(
                select(Case.student_id, func.count(Case.id)).where(
                    Case.campus_id == ctx.campus_id, Case.assigned_counsellor_id == ctx.user_id,
                    Case.status.notin_(TERMINAL_STATES), Case.student_id.in_([s.id for s in students]),
                ).group_by(Case.student_id)
            )
            counts = {sid: n for sid, n in rows.all()}
        return [
            StudentItem(student_id=s.id, student_ref=s.student_uid, full_name=s.full_name, department=s.department,
                        cohort_code=s.cohort_code, open_cases=counts.get(s.id, 0))
            for s in students
        ]

    @staticmethod
    async def list_followups(
        db: AsyncSession, ctx: TenancyContext, upcoming_only: bool, limit: int, offset: int
    ):
        owner = CaseloadService._owner(ctx, None)
        stmt = select(FollowUp).where(FollowUp.campus_id == ctx.campus_id)
        if owner:
            stmt = stmt.where(FollowUp.counsellor_id == owner)
        if upcoming_only:
            stmt = stmt.where(FollowUp.status == "scheduled").order_by(FollowUp.scheduled_at)
        else:
            stmt = stmt.order_by(FollowUp.scheduled_at.desc())
        rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
        return [FollowUpService.to_out(f, ctx) for f in rows]

    @staticmethod
    async def dashboard(db: AsyncSession, ctx: TenancyContext) -> CounsellorDashboard:
        if ctx.role != Role.COUNSELLOR:
            raise PermissionDeniedError("The dashboard is the counsellor's own view; admins use /campus/dashboard")
        now = utc_now()
        cases = list((await db.execute(
            select(Case).where(
                Case.campus_id == ctx.campus_id, Case.assigned_counsellor_id == ctx.user_id,
                Case.status.notin_(TERMINAL_STATES),
            )
        )).scalars().all())
        overdue = [c for c in cases if c.due_date and aware(c.due_date) < now]
        escalated = [c for c in cases if c.escalated_deadline_version is not None
                     and c.escalated_deadline_version == c.deadline_version]
        fups = list((await db.execute(
            select(FollowUp).where(
                FollowUp.campus_id == ctx.campus_id, FollowUp.counsellor_id == ctx.user_id, FollowUp.status == "scheduled"
            ).order_by(FollowUp.scheduled_at)
        )).scalars().all())
        sessions = list((await db.execute(
            select(CounsellingSession).where(
                CounsellingSession.campus_id == ctx.campus_id, CounsellingSession.counsellor_id == ctx.user_id,
                CounsellingSession.status == "scheduled", CounsellingSession.scheduled_at >= now,
            ).order_by(CounsellingSession.scheduled_at)
        )).scalars().all())
        unread = (await db.execute(
            select(func.count(Notification.id)).where(
                Notification.recipient_id == ctx.user_id, Notification.campus_id == ctx.campus_id,
                Notification.is_read == False,  # noqa: E712
            )
        )).scalar_one()
        week = now + timedelta(days=7)
        return CounsellorDashboard(
            active_cases=len(cases), overdue_cases=len(overdue), escalated_cases=len(escalated),
            upcoming_sessions=sum(1 for s in sessions if aware(s.scheduled_at) <= week),
            overdue_followups=sum(1 for f in fups if aware(f.scheduled_at) < now),
            unread_notifications=unread,
            upcoming_followups=[FollowUpService.to_out(f, ctx) for f in fups if aware(f.scheduled_at) >= now][:5],
            next_sessions=[_session_out(s) for s in sessions[:5]],
        )


# --------------------------------------------------------------- sessions
def _session_out(s: CounsellingSession) -> SessionOut:
    return SessionOut(
        id=s.id, student_id=s.student_id, student_name=s.student.full_name if s.student else None, case_id=s.case_id,
        counsellor_id=s.counsellor_id, scheduled_at=s.scheduled_at, duration_minutes=s.duration_minutes, mode=s.mode,
        location=s.location, status=s.status, cancel_reason=s.cancel_reason, completed_at=s.completed_at,
        created_at=s.created_at,
    )


async def _assert_no_overlap(
    db: AsyncSession, campus_id: str, counsellor_id: str, start: datetime, minutes: int, exclude_id: Optional[str] = None
) -> None:
    start = aware(start)
    end = start + timedelta(minutes=minutes)
    stmt = select(CounsellingSession).where(
        CounsellingSession.campus_id == campus_id, CounsellingSession.counsellor_id == counsellor_id,
        CounsellingSession.status == "scheduled",
        CounsellingSession.scheduled_at > start - timedelta(hours=5),
        CounsellingSession.scheduled_at < end,
    )
    for other in (await db.execute(stmt)).scalars().all():
        if other.id == exclude_id:
            continue
        o_start = aware(other.scheduled_at)
        if o_start < end and o_start + timedelta(minutes=other.duration_minutes) > start:
            raise DishaBaseException("The counsellor already has a session in that time slot", 409)


async def _notify_student(db, session: CounsellingSession, template: str, suffix: str) -> None:
    student = (await db.execute(select(Student).where(Student.id == session.student_id))).scalar_one_or_none()
    if student and student.user_id:
        await NotificationOutboxService.enqueue(
            db, campus_id=session.campus_id, recipient_id=student.user_id, template_key=template,
            safe_payload={"session_id": session.id, "scheduled_at": aware(session.scheduled_at).strftime("%d %b %Y %H:%M UTC"),
                          "reference_type": "session", "reference_id": session.id},
            idempotency_key=f"session-{session.id}-{suffix}",
        )


async def _own_session(db: AsyncSession, ctx: TenancyContext, session_id: str) -> CounsellingSession:
    res = await db.execute(
        select(CounsellingSession).where(CounsellingSession.id == session_id, CounsellingSession.campus_id == ctx.campus_id)
    )
    s = res.scalar_one_or_none()
    if not s:
        raise EntityNotFoundError("Session", session_id)
    if ctx.role not in SUPERVISORS and s.counsellor_id != ctx.user_id:
        raise PermissionDeniedError("Only the session's counsellor (or an HOD) may change it")
    return s


class SessionService:
    @staticmethod
    async def create(db: AsyncSession, ctx: TenancyContext, data: SessionCreate) -> SessionOut:
        counsellor_id = data.counsellor_id or ctx.user_id
        is_supervisor = ctx.role in SUPERVISORS
        if counsellor_id != ctx.user_id and not is_supervisor:
            raise PermissionDeniedError("Only an HOD or platform admin may schedule for another counsellor")
        if ctx.role not in (Role.COUNSELLOR, *SUPERVISORS):
            raise PermissionDeniedError("Role may not schedule counselling sessions")
        await _require_counsellor_member(db, ctx.campus_id, counsellor_id)
        student = await _student(db, ctx.campus_id, data.student_id)
        if not is_supervisor and not await student_in_scope(db, ctx.campus_id, counsellor_id, student.id):
            raise PermissionDeniedError("This student is not on your caseload")
        if aware(data.scheduled_at) < utc_now() - timedelta(minutes=1):
            raise DishaBaseException("scheduled_at must be in the future", 422)
        if data.case_id:
            case = await load_case(db, ctx.campus_id, data.case_id)
            if case.student_id != student.id:
                raise DishaBaseException("The case belongs to a different student", 422)
            if case.status in TERMINAL_STATES:
                raise StateTransitionError(case.status, case.status, "The case is closed or dismissed")
            assert_case_writer(ctx, case)
        await _assert_no_overlap(db, ctx.campus_id, counsellor_id, data.scheduled_at, data.duration_minutes)

        s = CounsellingSession(
            campus_id=ctx.campus_id, student_id=student.id, case_id=data.case_id, counsellor_id=counsellor_id,
            scheduled_at=data.scheduled_at, duration_minutes=data.duration_minutes, mode=data.mode,
            location=data.location, status="scheduled", created_by=ctx.user_id,
        )
        db.add(s)
        await db.flush()
        await db.refresh(s)
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counselling_session", entity_id=s.id,
            action="SESSION_SCHEDULED",
            event_metadata={"student_id": student.id, "case_id": data.case_id, "mode": data.mode,
                            "scheduled_at": aware(data.scheduled_at).isoformat()},
        )
        await _notify_student(db, s, "SESSION_SCHEDULED", "scheduled")
        return _session_out(s)

    @staticmethod
    async def list(
        db: AsyncSession, ctx: TenancyContext, status: Optional[str], from_: Optional[datetime], to: Optional[datetime],
        student_id: Optional[str], counsellor_id: Optional[str], limit: int, offset: int,
    ) -> List[SessionOut]:
        stmt = select(CounsellingSession).where(CounsellingSession.campus_id == ctx.campus_id)
        if ctx.role == Role.COUNSELLOR:
            if counsellor_id and counsellor_id != ctx.user_id:
                raise PermissionDeniedError("Counsellors can only list their own sessions")
            stmt = stmt.where(CounsellingSession.counsellor_id == ctx.user_id)
        elif counsellor_id:
            stmt = stmt.where(CounsellingSession.counsellor_id == counsellor_id)
        if status:
            stmt = stmt.where(CounsellingSession.status == status)
        if from_:
            stmt = stmt.where(CounsellingSession.scheduled_at >= from_)
        if to:
            stmt = stmt.where(CounsellingSession.scheduled_at <= to)
        if student_id:
            stmt = stmt.where(CounsellingSession.student_id == student_id)
        stmt = stmt.order_by(CounsellingSession.scheduled_at).limit(limit).offset(offset)
        return [_session_out(s) for s in (await db.execute(stmt)).scalars().all()]

    @staticmethod
    async def get(db: AsyncSession, ctx: TenancyContext, session_id: str) -> SessionOut:
        res = await db.execute(
            select(CounsellingSession).where(
                CounsellingSession.id == session_id, CounsellingSession.campus_id == ctx.campus_id
            )
        )
        s = res.scalar_one_or_none()
        if not s:
            raise EntityNotFoundError("Session", session_id)
        if ctx.role == Role.COUNSELLOR and s.counsellor_id != ctx.user_id:
            raise EntityNotFoundError("Session", session_id)
        return _session_out(s)

    @staticmethod
    async def reschedule(db: AsyncSession, ctx: TenancyContext, session_id: str, data: SessionReschedule) -> SessionOut:
        s = await _own_session(db, ctx, session_id)
        if s.status != "scheduled":
            raise StateTransitionError(s.status, "scheduled", "Only scheduled sessions can be rescheduled")
        if aware(data.scheduled_at) < utc_now() - timedelta(minutes=1):
            raise DishaBaseException("scheduled_at must be in the future", 422)
        minutes = data.duration_minutes or s.duration_minutes
        await _assert_no_overlap(db, ctx.campus_id, s.counsellor_id, data.scheduled_at, minutes, exclude_id=s.id)
        s.scheduled_at = data.scheduled_at
        s.duration_minutes = minutes
        if data.location is not None:
            s.location = data.location
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counselling_session", entity_id=s.id,
            action="SESSION_RESCHEDULED", event_metadata={"scheduled_at": aware(data.scheduled_at).isoformat()},
        )
        await db.flush()
        await _notify_student(db, s, "SESSION_RESCHEDULED", f"rescheduled-{int(aware(data.scheduled_at).timestamp())}")
        return _session_out(s)

    @staticmethod
    async def cancel(db: AsyncSession, ctx: TenancyContext, session_id: str, data: SessionCancel) -> SessionOut:
        s = await _own_session(db, ctx, session_id)
        if s.status != "scheduled":
            raise StateTransitionError(s.status, "cancelled", "Only scheduled sessions can be cancelled")
        s.status = "cancelled"
        s.cancel_reason = data.reason
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counselling_session", entity_id=s.id,
            action="SESSION_CANCELLED", event_metadata={},
        )
        await db.flush()
        await _notify_student(db, s, "SESSION_CANCELLED", "cancelled")
        return _session_out(s)

    @staticmethod
    async def _close(db, ctx, session_id: str, new_status: str, action: str) -> SessionOut:
        s = await _own_session(db, ctx, session_id)
        if s.status != "scheduled":
            raise StateTransitionError(s.status, new_status, f"Only scheduled sessions can be marked {new_status}")
        if aware(s.scheduled_at) > utc_now() + timedelta(minutes=15):
            raise StateTransitionError(s.status, new_status, "The session has not started yet")
        s.status = new_status
        if new_status == "completed":
            s.completed_at = utc_now()
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counselling_session", entity_id=s.id,
            action=action, event_metadata={"case_id": s.case_id},
        )
        await db.flush()
        return _session_out(s)

    @staticmethod
    async def complete(db, ctx, session_id: str) -> SessionOut:
        return await SessionService._close(db, ctx, session_id, "completed", "SESSION_COMPLETED")

    @staticmethod
    async def no_show(db, ctx, session_id: str) -> SessionOut:
        return await SessionService._close(db, ctx, session_id, "no_show", "SESSION_NO_SHOW")


# ------------------------------------------------------------------ notes
def _assert_counsellor_only(ctx: TenancyContext) -> None:
    # Deliberately strict: platform admins and institution admins do not read clinical notes.
    if ctx.role != Role.COUNSELLOR:
        raise PermissionDeniedError("Confidential counselling notes are restricted to counsellors")


class NoteService:
    @staticmethod
    async def create(db: AsyncSession, ctx: TenancyContext, data: NoteCreate) -> CounsellingNote:
        _assert_counsellor_only(ctx)
        student = await _student(db, ctx.campus_id, data.student_id)
        if not await student_in_scope(db, ctx.campus_id, ctx.user_id, student.id):
            raise PermissionDeniedError("This student is not on your caseload")
        if data.case_id:
            case = await load_case(db, ctx.campus_id, data.case_id)
            if case.student_id != student.id:
                raise DishaBaseException("The case belongs to a different student", 422)
        if data.session_id:
            sess = (await db.execute(
                select(CounsellingSession).where(
                    CounsellingSession.id == data.session_id, CounsellingSession.campus_id == ctx.campus_id,
                    CounsellingSession.student_id == student.id,
                )
            )).scalar_one_or_none()
            if not sess:
                raise EntityNotFoundError("Session", data.session_id)
        note = CounsellingNote(
            campus_id=ctx.campus_id, student_id=student.id, case_id=data.case_id, session_id=data.session_id,
            author_id=ctx.user_id, content=data.content,
        )
        db.add(note)
        await db.flush()
        # the audit trail records that a note exists, never what it says
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counselling_note", entity_id=note.id,
            action="COUNSELLING_NOTE_CREATED", event_metadata={"student_id": student.id, "case_id": data.case_id},
        )
        return note

    @staticmethod
    async def list_for_student(
        db: AsyncSession, ctx: TenancyContext, student_id: str, limit: int, offset: int
    ) -> List[CounsellingNote]:
        _assert_counsellor_only(ctx)
        student = await _student(db, ctx.campus_id, student_id)
        if not await student_in_scope(db, ctx.campus_id, ctx.user_id, student.id):
            raise PermissionDeniedError("This student is not on your caseload")
        rows = list((await db.execute(
            select(CounsellingNote).where(
                CounsellingNote.campus_id == ctx.campus_id, CounsellingNote.student_id == student.id
            ).order_by(CounsellingNote.created_at.desc()).limit(limit).offset(offset)
        )).scalars().all())
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="student", entity_id=student.id,
            action="COUNSELLING_NOTES_READ", event_metadata={"count": len(rows)},
        )
        return rows


# ------------------------------------------------------------ assignments
class AssignmentService:
    @staticmethod
    async def create(db: AsyncSession, ctx: TenancyContext, data: AssignmentCreate) -> CounsellorAssignment:
        await _require_counsellor_member(db, ctx.campus_id, data.counsellor_id)
        student = await _student(db, ctx.campus_id, data.student_id)
        dup = await db.execute(
            select(CounsellorAssignment.id).where(
                CounsellorAssignment.campus_id == ctx.campus_id, CounsellorAssignment.counsellor_id == data.counsellor_id,
                CounsellorAssignment.student_id == student.id, CounsellorAssignment.is_active == True,  # noqa: E712
            )
        )
        if dup.first():
            raise DishaBaseException("That counsellor is already assigned to the student", 409)
        a = CounsellorAssignment(
            campus_id=ctx.campus_id, counsellor_id=data.counsellor_id, student_id=student.id, is_active=True
        )
        db.add(a)
        await db.flush()
        await AuditService.record_event(
            db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counsellor_assignment", entity_id=a.id,
            action="COUNSELLOR_ASSIGNED", event_metadata={"counsellor_id": data.counsellor_id, "student_id": student.id},
        )
        return a

    @staticmethod
    async def list(
        db: AsyncSession, ctx: TenancyContext, counsellor_id: Optional[str], student_id: Optional[str],
        active_only: bool, limit: int, offset: int,
    ) -> List[CounsellorAssignment]:
        stmt = select(CounsellorAssignment).where(CounsellorAssignment.campus_id == ctx.campus_id)
        if counsellor_id:
            stmt = stmt.where(CounsellorAssignment.counsellor_id == counsellor_id)
        if student_id:
            stmt = stmt.where(CounsellorAssignment.student_id == student_id)
        if active_only:
            stmt = stmt.where(CounsellorAssignment.is_active == True)  # noqa: E712
        stmt = stmt.order_by(CounsellorAssignment.assigned_at.desc()).limit(limit).offset(offset)
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def end(db: AsyncSession, ctx: TenancyContext, assignment_id: str) -> CounsellorAssignment:
        res = await db.execute(
            select(CounsellorAssignment).where(
                CounsellorAssignment.id == assignment_id, CounsellorAssignment.campus_id == ctx.campus_id
            )
        )
        a = res.scalar_one_or_none()
        if not a:
            raise EntityNotFoundError("Assignment", assignment_id)
        if a.is_active:
            a.is_active = False
            await AuditService.record_event(
                db, actor_id=ctx.user_id, campus_id=ctx.campus_id, entity_type="counsellor_assignment", entity_id=a.id,
                action="COUNSELLOR_UNASSIGNED", event_metadata={"counsellor_id": a.counsellor_id, "student_id": a.student_id},
            )
        await db.flush()
        return a
