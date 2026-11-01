import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from sqlalchemy import select, update, and_, or_, false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload, selectinload

from app.shared.enums import CaseState, CaseStatus, map_status_to_state, map_state_to_status
from app.shared.utils import utc_now
from app.core.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ConcurrencyConflictError,
    StateTransitionError,
)
from app.core.permissions import Role
from app.modules.cases.state_machine import CaseStateMachine, TransitionRule
from app.modules.cases.models import Case, CaseEvent, CaseNote
from app.modules.audit.services import AuditService
from app.modules.notifications.services import NotificationOutboxService
from app.modules.cases.models import FollowUp, InterventionOutcome
from app.modules.cases.schemas import (
    CaseCreateRequest,
    CaseUpdateRequest,
    CaseAssignRequest,
    CaseReopenRequest,
    CaseDismissRequest,
    CaseDetailResponse,
    CaseEventResponse,
)


@asynccontextmanager
async def transaction_scope(db: AsyncSession):
    """Ensure atomic transaction boundaries. Automatically rolls back on any exception."""
    if db.in_transaction():
        async with db.begin_nested():
            yield
    else:
        async with db.begin():
            yield


def case_to_detail_response(case: Case) -> CaseDetailResponse:
    """Project authoritative SQLAlchemy Case ORM instance into CaseDetailResponse."""
    canonical_state = map_status_to_state(case.status)
    legacy_status = map_state_to_status(canonical_state.value)

    student_name = case.student.full_name if case.student else None
    student_ref = case.student.student_uid if case.student else None
    department = case.student.department if case.student else None
    owner_name = case.assigned_counsellor.full_name if case.assigned_counsellor else None

    is_overdue = False
    if case.due_date and canonical_state not in (CaseState.CLOSED, CaseState.DISMISSED):
        now_dt = utc_now()
        due = case.due_date if case.due_date.tzinfo else case.due_date.replace(tzinfo=timezone.utc)
        if due < now_dt:
            is_overdue = True

    return CaseDetailResponse(
        id=case.id,
        campus_id=case.campus_id,
        student_id=case.student_id,
        student_name=student_name,
        student_ref=student_ref,
        department=department,
        state=canonical_state,
        legacy_status=legacy_status,
        priority=case.priority,
        primary_owner_user_id=case.assigned_counsellor_id,
        owner_name=owner_name,
        due_at=case.due_date,
        is_overdue=is_overdue,
        is_escalated=(case.escalated_deadline_version is not None
                      and case.escalated_deadline_version == case.deadline_version),
        selected_intervention_key=None,
        version=case.version,
        created_at=case.created_at,
        updated_at=case.updated_at,
        closed_at=case.closed_at,
        closed_by=case.closed_by,
    )


def _as_utc(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def _case_has_support_follow_up(db: AsyncSession, case_id: str, campus_id: str) -> bool:
    res = await db.execute(
        select(FollowUp.id).where(
            FollowUp.case_id == case_id,
            FollowUp.campus_id == campus_id,
            FollowUp.follow_up_type == "support_delivered",
            FollowUp.status == "completed",
        ).limit(1)
    )
    return res.scalar_one_or_none() is not None


async def _case_has_outcome(db: AsyncSession, case_id: str, campus_id: str) -> bool:
    res = await db.execute(
        select(InterventionOutcome.id).where(
            InterventionOutcome.case_id == case_id, InterventionOutcome.campus_id == campus_id
        ).limit(1)
    )
    return res.scalar_one_or_none() is not None


class CaseLifecycleService:
    """Centralized Case Lifecycle & State Machine Service for DISHA."""

    @staticmethod
    def transition_case(
        case: Dict[str, Any],
        target_state_raw: str,
        expected_version: int,
        actor_user_id: str,
        actor_roles: List[str],
        actor_campus_id: str,
        reason_code: Optional[str] = None,
        notes: Optional[str] = None,
        new_owner_id: Optional[str] = None,
        due_at: Optional[datetime] = None,
        has_follow_up: bool = False,
        has_outcome: bool = False,
        is_override: bool = False
    ) -> Dict[str, Any]:
        """
        Execute deterministic case state transition with guard checks, tenancy enforcement,
        optimistic locking, and event preparation (synchronous dictionary evaluator).
        """
        # 1. Tenancy validation
        case_campus_id = case.get("campus_id") or case.get("institution_id")
        if case_campus_id != actor_campus_id and "platform_admin" not in actor_roles:
            raise PermissionDeniedError("Case does not belong to your institutional campus scope")

        # 2. Optimistic Concurrency Check (HTTP 409 on version mismatch)
        current_version = case.get("version", 1)
        if current_version != expected_version:
            raise ConcurrencyConflictError(
                f"Optimistic lock conflict: Expected version {expected_version}, but case has version {current_version}"
            )

        # 3. Canonical state resolution
        current_state_raw = case.get("state") or case.get("status")
        current_state = map_status_to_state(current_state_raw)
        target_state = map_status_to_state(target_state_raw)

        # 4. Guard and Transition Validation
        owner_id = case.get("primary_owner_user_id") or case.get("assigned_counsellor_id")
        effective_owner = new_owner_id or owner_id
        effective_due_at = due_at or case.get("due_at") or case.get("due_date")

        has_note_flag = bool(notes or reason_code)

        rule = CaseStateMachine.validate_transition(
            from_state=current_state,
            to_state=target_state,
            actor_roles=actor_roles,
            actor_user_id=actor_user_id,
            owner_user_id=owner_id,
            has_due_date=bool(effective_due_at),
            has_case_note=has_note_flag,
            has_follow_up=has_follow_up,
            has_outcome=has_outcome,
            is_override=is_override
        )

        # 5. Mutate state atomically
        now = utc_now()
        case["state"] = target_state.value
        case["status"] = target_state.value
        case["legacy_status"] = map_state_to_status(target_state.value).value
        case["version"] = current_version + 1
        case["updated_at"] = now

        if new_owner_id:
            case["primary_owner_user_id"] = new_owner_id
            case["assigned_counsellor_id"] = new_owner_id

        if due_at:
            case["due_at"] = due_at
            case["due_date"] = due_at

        if target_state == CaseState.ACCEPTED:
            case["accepted_at"] = now

        if target_state in (CaseState.CLOSED, CaseState.DISMISSED):
            case["closed_at"] = now
            case["closed_by"] = actor_user_id

        # 6. Event metadata
        event_record = {
            "id": str(uuid.uuid4()),
            "case_id": case.get("id"),
            "campus_id": case_campus_id,
            "actor_id": actor_user_id,
            "event_type": rule.event_type,
            "from_state": current_state.value,
            "to_state": target_state.value,
            "reason_code": reason_code,
            "metadata": {
                "notes": notes,
                "version": case["version"],
                "new_owner_id": new_owner_id
            },
            "created_at": now
        }

        # 7. Notification intent determination
        notification_intent = None
        if rule.generates_notification:
            if target_state == CaseState.ASSIGNED:
                notification_intent = {
                    "recipient_id": effective_owner,
                    "title": "New Case Assigned",
                    "category": "case_assigned"
                }
            elif target_state == CaseState.CLOSED:
                notification_intent = {
                    "recipient_id": owner_id or actor_user_id,
                    "title": "Case Closed",
                    "category": "case_closed"
                }

        return {
            "case": case,
            "event": event_record,
            "rule": rule,
            "notification_intent": notification_intent
        }


CASE_WIDE_VIEW_ROLES = {"platform_admin", "institution_admin", "hod", "leadership"}


class CaseService:
    """Production database-backed Case service with ACID transaction boundaries,
    strict campus isolation, and atomic optimistic concurrency."""

    @staticmethod
    async def create_case(
        db: AsyncSession,
        campus_id: str,
        actor_id: str,
        actor_roles: List[str],
        data: CaseCreateRequest,
    ) -> Case:
        """Create a new case in persistent database storage with transactional CaseEvent and AuditEvent."""
        allowed_creator_roles = {
            Role.PLATFORM_ADMIN.value,
            Role.INSTITUTION_ADMIN.value,
            Role.HOD.value,
            Role.COUNSELLOR.value,
            Role.FACULTY.value,
            Role.MENTOR.value,
        }
        if not any(r in allowed_creator_roles for r in actor_roles) and Role.PLATFORM_ADMIN.value not in actor_roles:
            raise PermissionDeniedError("Insufficient permissions to create a case")

        target_state = map_status_to_state(data.initial_state or CaseState.ACTION_PLANNED.value)
        now = utc_now()
        case_id = str(uuid.uuid4())

        case = Case(
            id=case_id,
            campus_id=campus_id,
            student_id=data.student_id,
            assigned_counsellor_id=data.assigned_counsellor_id,
            status=target_state.value,
            priority=data.priority or "medium",
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            version=1,
            created_at=now,
            updated_at=now,
        )

        async with transaction_scope(db):
            db.add(case)
            await db.flush()

            # CaseEvent
            event = CaseEvent(
                id=str(uuid.uuid4()),
                case_id=case.id,
                actor_id=actor_id,
                campus_id=campus_id,
                event_type="CASE_CREATED",
                payload={
                    "from_state": "",
                    "to_state": target_state.value,
                    "metadata": {"version": 1},
                },
                created_at=now,
            )
            db.add(event)

            # AuditEvent via authoritative AuditService (strictly non-confidential)
            await AuditService.record_event(
                db=db,
                actor_id=actor_id,
                campus_id=campus_id,
                entity_type="case",
                entity_id=case.id,
                action="CASE_CREATED",
                event_metadata={
                    "status": target_state.value,
                    "version": 1,
                    "assigned_counsellor_id": data.assigned_counsellor_id,
                },
            )

            # Notification outbox intent if assigned (delivered by the worker)
            if data.assigned_counsellor_id:
                await NotificationOutboxService.enqueue(
                    db,
                    campus_id=campus_id,
                    recipient_id=data.assigned_counsellor_id,
                    template_key="CASE_ASSIGNED",
                    safe_payload={"case_id": case.id, "from_state": "", "to_state": target_state.value},
                    idempotency_key=f"case-{case.id}-v1-assigned",
                    case_id=case.id,
                )

        # Reload with relations
        return await CaseService.get_case(db, case.id, campus_id, is_platform_admin=True)

    @staticmethod
    async def get_case(
        db: AsyncSession,
        case_id: str,
        campus_id: str,
        is_platform_admin: bool = False,
    ) -> Case:
        """Retrieve a case by ID enforcing campus isolation."""
        stmt = (
            select(Case)
            .options(selectinload(Case.student), selectinload(Case.assigned_counsellor))
            .where(Case.id == case_id)
        )
        if not is_platform_admin:
            stmt = stmt.where(Case.campus_id == campus_id)

        result = await db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            raise EntityNotFoundError("Case", case_id)
        return case

    @staticmethod
    async def list_cases(
        db: AsyncSession,
        campus_id: str,
        actor_id: str,
        actor_roles: List[str],
        is_platform_admin: bool = False,
        state: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority: Optional[str] = None,
        student_id: Optional[str] = None,
        assigned_counsellor_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Case]:
        """List cases strictly isolated by campus tenancy and optional filters."""
        # The list view needs only the student and owner names: stop the eager-load cascade (notes, events, ...).
        stmt = (
            select(Case)
            .options(
                lazyload("*"),
                selectinload(Case.student).options(lazyload("*")),
                selectinload(Case.assigned_counsellor).options(lazyload("*")),
            )
        )
        if not is_platform_admin or campus_id:
            stmt = stmt.where(Case.campus_id == campus_id)

        # Visibility by role: a case holds sensitive student information.
        roles = set(actor_roles or [])
        if not (is_platform_admin or roles & CASE_WIDE_VIEW_ROLES):
            if roles & {"counsellor", "mentor"}:
                stmt = stmt.where(or_(Case.assigned_counsellor_id == actor_id, Case.assigned_counsellor_id.is_(None)))
            elif "faculty" in roles:
                from app.modules.faculty.models import CourseEnrollment, CourseSection
                taught = (
                    select(CourseEnrollment.student_id)
                    .join(CourseSection, CourseSection.id == CourseEnrollment.section_id)
                    .where(CourseSection.faculty_id == actor_id)
                )
                stmt = stmt.where(Case.student_id.in_(taught))
            else:
                stmt = stmt.where(false())

        if state:
            canonical_state = map_status_to_state(state)
            stmt = stmt.where(Case.status == canonical_state.value)
        elif status_filter:
            canonical_state = map_status_to_state(status_filter)
            stmt = stmt.where(Case.status == canonical_state.value)

        if priority:
            stmt = stmt.where(Case.priority == priority)

        if student_id:
            stmt = stmt.where(Case.student_id == student_id)

        if assigned_counsellor_id:
            stmt = stmt.where(Case.assigned_counsellor_id == assigned_counsellor_id)

        stmt = stmt.order_by(Case.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_case(
        db: AsyncSession,
        case_id: str,
        campus_id: str,
        actor_id: str,
        actor_roles: List[str],
        data: CaseUpdateRequest,
        is_platform_admin: bool = False,
    ) -> Case:
        """Update case metadata using atomic database-level optimistic locking."""
        now = utc_now()
        values: Dict[str, Any] = {
            "version": Case.version + 1,
            "updated_at": now,
        }
        if data.title is not None:
            values["title"] = data.title
        if data.description is not None:
            values["description"] = data.description
        if data.priority is not None:
            values["priority"] = data.priority
        if data.due_date is not None:
            values["due_date"] = data.due_date
            values["deadline_version"] = Case.deadline_version + 1  # re-arms escalation (ESC-02)

        where_cond = [Case.id == case_id, Case.version == data.expected_version]
        if not is_platform_admin:
            where_cond.append(Case.campus_id == campus_id)

        async with transaction_scope(db):
            stmt = update(Case).where(*where_cond).values(**values)
            res = await db.execute(stmt)
            if res.rowcount == 0:
                check_stmt = select(Case.version).where(Case.id == case_id)
                if not is_platform_admin:
                    check_stmt = check_stmt.where(Case.campus_id == campus_id)
                cur_ver = await db.scalar(check_stmt)
                if cur_ver is None:
                    raise EntityNotFoundError("Case", case_id)
                raise ConcurrencyConflictError(
                    f"Optimistic lock conflict: Expected version {data.expected_version}, but case has version {cur_ver}"
                )

            # Persist CaseEvent
            event = CaseEvent(
                id=str(uuid.uuid4()),
                case_id=case_id,
                actor_id=actor_id,
                campus_id=campus_id,
                event_type="CASE_UPDATED",
                payload={"metadata": {"version": data.expected_version + 1}},
                created_at=now,
            )
            db.add(event)

            # Persist AuditEvent via authoritative AuditService
            await AuditService.record_event(
                db=db,
                actor_id=actor_id,
                campus_id=campus_id,
                entity_type="case",
                entity_id=case_id,
                action="CASE_UPDATED",
                event_metadata={"version": data.expected_version + 1},
            )

        return await CaseService.get_case(db, case_id, campus_id, is_platform_admin)

    @staticmethod
    async def transition_case_db(
        db: AsyncSession,
        case_id: str,
        campus_id: str,
        actor_user_id: str,
        actor_roles: List[str],
        target_state_raw: str,
        expected_version: int,
        reason_code: Optional[str] = None,
        notes: Optional[str] = None,
        new_owner_id: Optional[str] = None,
        due_at: Optional[datetime] = None,
        has_follow_up: bool = False,
        has_outcome: bool = False,
        is_override: bool = False,
        is_platform_admin: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute deterministic state transition with database-level atomic conditional locking,
        comprehensive guard validation, and transactional synchronization across Case,
        CaseEvent, AuditEvent, and Notification outbox.
        """
        # 1. Tenancy validation & guard check
        check_stmt = select(Case).where(Case.id == case_id)
        if not is_platform_admin:
            check_stmt = check_stmt.where(Case.campus_id == campus_id)

        res = await db.execute(check_stmt)
        case = res.scalar_one_or_none()
        if not case:
            raise EntityNotFoundError("Case", case_id)

        if case.campus_id != campus_id and not is_platform_admin:
            raise PermissionDeniedError("Case does not belong to your institutional campus scope")

        # 2. Canonical state resolution & guard evaluation
        current_state = map_status_to_state(case.status)
        target_state = map_status_to_state(target_state_raw)

        owner_id = case.assigned_counsellor_id
        effective_owner = new_owner_id or owner_id
        effective_due_at = due_at or case.due_date
        has_note_flag = bool(notes or reason_code)

        # Guard facts come from the database (CASE-SM-03); a caller-supplied flag can only add to them
        has_follow_up = has_follow_up or await _case_has_support_follow_up(db, case_id, case.campus_id)
        has_outcome = has_outcome or await _case_has_outcome(db, case_id, case.campus_id)

        rule = CaseStateMachine.validate_transition(
            from_state=current_state,
            to_state=target_state,
            actor_roles=actor_roles,
            actor_user_id=actor_user_id,
            owner_user_id=owner_id,
            has_due_date=bool(effective_due_at),
            has_case_note=has_note_flag,
            has_follow_up=has_follow_up,
            has_outcome=has_outcome,
            is_override=is_override,
        )

        now = utc_now()
        upd_vals: Dict[str, Any] = {
            "status": target_state.value,
            "version": Case.version + 1,
            "updated_at": now,
        }
        if new_owner_id:
            upd_vals["assigned_counsellor_id"] = new_owner_id
        if due_at:
            upd_vals["due_date"] = due_at
            if case.due_date is None or _as_utc(case.due_date) != _as_utc(due_at):
                upd_vals["deadline_version"] = Case.deadline_version + 1  # re-arms escalation (ESC-02)
        if target_state in (CaseState.CLOSED, CaseState.DISMISSED):
            upd_vals["closed_at"] = now
            upd_vals["closed_by"] = actor_user_id

        event_id = str(uuid.uuid4())

        # 3. Transaction Boundary: Atomically execute update and child entity insertions
        async with transaction_scope(db):
            # Atomic conditional update on id + campus_id + version
            upd_stmt = (
                update(Case)
                .where(
                    Case.id == case_id,
                    Case.campus_id == case.campus_id,
                    Case.version == expected_version,
                )
                .values(**upd_vals)
            )
            upd_res = await db.execute(upd_stmt)
            if upd_res.rowcount == 0:
                cur_ver = await db.scalar(
                    select(Case.version).where(Case.id == case_id, Case.campus_id == case.campus_id)
                )
                if cur_ver is None:
                    raise EntityNotFoundError("Case", case_id)
                raise ConcurrencyConflictError(
                    f"Optimistic lock conflict: Expected version {expected_version}, but case has version {cur_ver}"
                )

            # Persist CaseEvent
            case_event = CaseEvent(
                id=event_id,
                case_id=case_id,
                actor_id=actor_user_id,
                campus_id=case.campus_id,
                event_type=rule.event_type,
                payload={
                    "from_state": current_state.value,
                    "to_state": target_state.value,
                    "reason_code": reason_code,
                    "metadata": {
                        "version": expected_version + 1,
                        "new_owner_id": new_owner_id,
                    },
                },
                created_at=now,
            )
            db.add(case_event)

            # Persist CaseNote if note provided (stored in dedicated confidential table)
            if notes:
                case_note = CaseNote(
                    id=str(uuid.uuid4()),
                    case_id=case_id,
                    author_id=actor_user_id,
                    campus_id=case.campus_id,
                    content=notes,
                    created_at=now,
                    updated_at=now,
                )
                db.add(case_note)

            # Persist AuditEvent via authoritative AuditService (strictly NON-CONFIDENTIAL metadata, NO clinical notes)
            audit_metadata = {
                "from_state": current_state.value,
                "to_state": target_state.value,
                "reason_code": reason_code,
                "version": expected_version + 1,
                "new_owner_id": new_owner_id,
            }
            await AuditService.record_event(
                db=db,
                actor_id=actor_user_id,
                campus_id=case.campus_id,
                entity_type="case",
                entity_id=case_id,
                action=rule.event_type,
                event_metadata=audit_metadata,
            )

            # Persist Notification outbox entry
            notification_intent = None
            if rule.generates_notification:
                recipient = None
                notif_title = ""
                if target_state == CaseState.ASSIGNED:
                    recipient = effective_owner
                    notif_title = "New Case Assigned"
                elif target_state in (CaseState.CLOSED, CaseState.DISMISSED):
                    recipient = owner_id or actor_user_id
                    notif_title = f"Case {target_state.value.capitalize()}"
                elif target_state == CaseState.REOPENED:
                    recipient = owner_id or actor_user_id
                    notif_title = "Case Reopened"

                if recipient:
                    notification_intent = {
                        "recipient_id": recipient,
                        "title": notif_title,
                        "category": f"case_{target_state.value}",
                    }
                    await NotificationOutboxService.enqueue(
                        db,
                        campus_id=case.campus_id,
                        recipient_id=recipient,
                        template_key=f"CASE_{target_state.value.upper()}",
                        safe_payload={
                            "case_id": case_id,
                            "from_state": current_state.value,
                            "to_state": target_state.value,
                        },
                        idempotency_key=f"case-{case_id}-v{expected_version + 1}-{target_state.value}",
                        case_id=case_id,
                    )

        # 4. Construct updated case state representation
        updated_case = await CaseService.get_case(db, case_id, campus_id, is_platform_admin)
        case_dict = {
            "id": updated_case.id,
            "campus_id": updated_case.campus_id,
            "student_id": updated_case.student_id,
            "state": target_state.value,
            "status": target_state.value,
            "legacy_status": map_state_to_status(target_state.value).value,
            "priority": updated_case.priority,
            "primary_owner_user_id": updated_case.assigned_counsellor_id,
            "assigned_counsellor_id": updated_case.assigned_counsellor_id,
            "due_at": updated_case.due_date,
            "due_date": updated_case.due_date,
            "version": updated_case.version,
            "created_at": updated_case.created_at,
            "updated_at": updated_case.updated_at,
            "closed_at": updated_case.closed_at,
            "closed_by": updated_case.closed_by,
        }

        event_dict = {
            "id": event_id,
            "case_id": case_id,
            "actor_id": actor_user_id,
            "event_type": rule.event_type,
            "from_state": current_state.value,
            "to_state": target_state.value,
            "reason_code": reason_code,
            "metadata": {
                "version": expected_version + 1,
                "new_owner_id": new_owner_id,
            },
            "created_at": now,
        }

        return {
            "case": case_dict,
            "event": event_dict,
            "rule": rule,
            "notification_intent": notification_intent,
        }

    @staticmethod
    async def assign_case(
        db: AsyncSession,
        case_id: str,
        campus_id: str,
        actor_id: str,
        actor_roles: List[str],
        data: CaseAssignRequest,
        is_platform_admin: bool = False,
    ) -> Case:
        """Assign or reassign a case to a counsellor."""
        await CaseService.transition_case_db(
            db=db,
            case_id=case_id,
            campus_id=campus_id,
            actor_user_id=actor_id,
            actor_roles=actor_roles,
            target_state_raw=CaseState.ASSIGNED.value,
            expected_version=data.expected_version,
            notes=data.notes,
            new_owner_id=data.counsellor_id,
            due_at=data.due_date,
            is_platform_admin=is_platform_admin,
        )
        return await CaseService.get_case(db, case_id, campus_id, is_platform_admin)

    @staticmethod
    async def reopen_case(
        db: AsyncSession,
        case_id: str,
        campus_id: str,
        actor_id: str,
        actor_roles: List[str],
        data: CaseReopenRequest,
        is_platform_admin: bool = False,
    ) -> Case:
        """Formally reopen a closed case."""
        await CaseService.transition_case_db(
            db=db,
            case_id=case_id,
            campus_id=campus_id,
            actor_user_id=actor_id,
            actor_roles=actor_roles,
            target_state_raw=CaseState.REOPENED.value,
            expected_version=data.expected_version,
            reason_code=data.reason_code,
            notes=data.notes,
            is_platform_admin=is_platform_admin,
        )
        return await CaseService.get_case(db, case_id, campus_id, is_platform_admin)

    @staticmethod
    async def dismiss_case(
        db: AsyncSession,
        case_id: str,
        campus_id: str,
        actor_id: str,
        actor_roles: List[str],
        data: CaseDismissRequest,
        is_platform_admin: bool = False,
    ) -> Case:
        """Dismiss a case early with mandatory rationale."""
        await CaseService.transition_case_db(
            db=db,
            case_id=case_id,
            campus_id=campus_id,
            actor_user_id=actor_id,
            actor_roles=actor_roles,
            target_state_raw=CaseState.DISMISSED.value,
            expected_version=data.expected_version,
            reason_code=data.reason_code,
            notes=data.notes,
            is_platform_admin=is_platform_admin,
        )
        return await CaseService.get_case(db, case_id, campus_id, is_platform_admin)

    @staticmethod
    async def get_case_events(
        db: AsyncSession,
        case_id: str,
        campus_id: str,
        is_platform_admin: bool = False,
    ) -> List[CaseEventResponse]:
        """Retrieve audit history of events for a case."""
        # Ensure case exists and tenancy is checked
        await CaseService.get_case(db, case_id, campus_id, is_platform_admin)

        stmt = select(CaseEvent).where(CaseEvent.case_id == case_id)
        if not is_platform_admin:
            stmt = stmt.where(CaseEvent.campus_id == campus_id)
        stmt = stmt.order_by(CaseEvent.created_at.asc())

        res = await db.execute(stmt)
        events = res.scalars().all()
        responses = []
        for ev in events:
            payload = ev.payload or {}
            responses.append(
                CaseEventResponse(
                    id=ev.id,
                    case_id=ev.case_id,
                    actor_id=ev.actor_id,
                    event_type=ev.event_type,
                    from_state=payload.get("from_state", ""),
                    to_state=payload.get("to_state", ""),
                    reason_code=payload.get("reason_code"),
                    metadata=payload.get("metadata", {}),
                    created_at=ev.created_at,
                )
            )
        return responses
