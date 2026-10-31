import uuid
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.shared.utils import utc_now
from app.shared.enums import CaseState, CaseStatus
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from app.core.dependencies import (
    TenancyContext,
    verify_faculty_section_access,
    verify_faculty_student_access,
)
from app.modules.roster.models import Student, Observation
from app.modules.faculty.models import (
    FacultyProfile,
    Course,
    CourseSection,
    CourseEnrollment,
    StudentAttendanceRecord,
    Assessment,
    AssessmentSubmission,
)
from app.modules.cases.models import (
    Signal,
    Case,
    CaseEvent,
    Intervention,
    InterventionCatalogue,
    InterventionOutcome,
    FollowUp,
)
from app.modules.audit.models import AuditEvent
from app.modules.cases.services import CaseService, transaction_scope
from app.modules.faculty.schemas import (
    AttendanceRecordCreate,
    AssessmentCreate,
    MarkEntry,
    SignalReviewRequest,
    CaseTaskCreate,
    FollowUpCreate,
    CaseOutcomeCreate,
)


def compute_sha256(payload: Any) -> str:
    raw = json.dumps(payload, default=str, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class FacultyService:

    @staticmethod
    async def get_dashboard(db: AsyncSession, tenancy: TenancyContext) -> Dict[str, Any]:
        # 1. Sections taught by faculty
        sec_stmt = (
            select(CourseSection)
            .options(selectinload(CourseSection.course), selectinload(CourseSection.enrollments))
            .where(
                CourseSection.faculty_id == tenancy.user_id,
                CourseSection.campus_id == tenancy.campus_id,
            )
        )
        sections = (await db.execute(sec_stmt)).scalars().all()
        section_ids = [s.id for s in sections]

        # 2. Total unique students monitored
        total_students = 0
        if section_ids:
            stu_stmt = select(func.count(func.distinct(CourseEnrollment.student_id))).where(
                CourseEnrollment.section_id.in_(section_ids),
                CourseEnrollment.campus_id == tenancy.campus_id,
            )
            total_students = (await db.execute(stu_stmt)).scalar() or 0

        # 3. Active unreviewed signals count
        signals_count = 0
        if section_ids:
            sig_stmt = (
                select(func.count(Signal.id))
                .join(CourseEnrollment, CourseEnrollment.student_id == Signal.student_id)
                .where(
                    CourseEnrollment.section_id.in_(section_ids),
                    Signal.campus_id == tenancy.campus_id,
                    Signal.reviewed == False,  # noqa: E712
                )
            )
            signals_count = (await db.execute(sig_stmt)).scalar() or 0

        sections_data = []
        for s in sections:
            sections_data.append({
                "id": s.id,
                "section_code": s.section_code,
                "name": s.name,
                "course_title": s.course.title if s.course else "",
                "course_code": s.course.code if s.course else "",
                "enrollment_count": len(s.enrollments),
                "access_code": s.access_code,
                "color": s.color,
            })

        return {
            "metrics": {
                "active_courses": len(set(s.course_id for s in sections)),
                "active_sections": len(sections),
                "total_students_monitored": total_students,
                "unreviewed_signals": signals_count,
            },
            "sections": sections_data,
        }

    @staticmethod
    async def list_courses(db: AsyncSession, tenancy: TenancyContext) -> List[Dict[str, Any]]:
        stmt = (
            select(Course)
            .where(
                Course.primary_faculty_id == tenancy.user_id,
                Course.campus_id == tenancy.campus_id,
            )
        )
        courses = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "category": c.category,
                "credits": c.credits,
                "semester": c.semester,
            }
            for c in courses
        ]

    @staticmethod
    async def list_sections(db: AsyncSession, tenancy: TenancyContext) -> List[Dict[str, Any]]:
        stmt = (
            select(CourseSection)
            .options(selectinload(CourseSection.course))
            .where(
                CourseSection.faculty_id == tenancy.user_id,
                CourseSection.campus_id == tenancy.campus_id,
            )
        )
        sections = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": s.id,
                "section_code": s.section_code,
                "name": s.name,
                "course_id": s.course_id,
                "course_title": s.course.title if s.course else "",
                "term": s.term,
                "access_code": s.access_code,
                "subject": s.subject,
                "color": s.color,
            }
            for s in sections
        ]

    @staticmethod
    async def get_section_students(
        db: AsyncSession,
        section_id: str,
        tenancy: TenancyContext,
    ) -> List[Dict[str, Any]]:
        await verify_faculty_section_access(section_id, tenancy, db)

        stmt = (
            select(Student)
            .join(CourseEnrollment, CourseEnrollment.student_id == Student.id)
            .where(
                CourseEnrollment.section_id == section_id,
                CourseEnrollment.campus_id == tenancy.campus_id,
            )
        )
        students = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": st.id,
                "student_uid": st.student_uid,
                "full_name": st.full_name,
                "email": st.email,
                "department": st.department,
                "cohort_code": st.cohort_code,
                "attendance_rate": st.attendance_rate,
                "quiz_score_avg": st.quiz_score_avg,
                "enrollment_status": st.enrollment_status,
            }
            for st in students
        ]

    @staticmethod
    async def get_student_detail(
        db: AsyncSession,
        student_id: str,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        student = await verify_faculty_student_access(student_id, tenancy, db)
        return {
            "id": student.id,
            "student_uid": student.student_uid,
            "display_name": student.full_name,
            "full_name": student.full_name,
            "email": student.email,
            "department": student.department,
            "cohort_code": student.cohort_code,
            "attendance_rate": student.attendance_rate,
            "quiz_score_avg": student.quiz_score_avg,
            "enrollment_status": student.enrollment_status,
        }

    @staticmethod
    async def get_student_attendance(
        db: AsyncSession,
        student_id: str,
        tenancy: TenancyContext,
    ) -> List[Dict[str, Any]]:
        await verify_faculty_student_access(student_id, tenancy, db)

        stmt = (
            select(StudentAttendanceRecord)
            .join(CourseSection, CourseSection.id == StudentAttendanceRecord.section_id)
            .where(
                StudentAttendanceRecord.student_id == student_id,
                StudentAttendanceRecord.campus_id == tenancy.campus_id,
                CourseSection.faculty_id == tenancy.user_id,
            )
            .order_by(StudentAttendanceRecord.date.desc())
        )
        records = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": r.id,
                "section_id": r.section_id,
                "date": r.date,
                "status": r.status,
                "recorded_at": r.recorded_at,
            }
            for r in records
        ]

    @staticmethod
    async def get_student_academics(
        db: AsyncSession,
        student_id: str,
        tenancy: TenancyContext,
    ) -> List[Dict[str, Any]]:
        await verify_faculty_student_access(student_id, tenancy, db)

        stmt = (
            select(AssessmentSubmission)
            .join(Assessment, Assessment.id == AssessmentSubmission.assessment_id)
            .join(CourseSection, CourseSection.id == Assessment.section_id)
            .options(selectinload(AssessmentSubmission.assessment))
            .where(
                AssessmentSubmission.student_id == student_id,
                AssessmentSubmission.campus_id == tenancy.campus_id,
                CourseSection.faculty_id == tenancy.user_id,
            )
            .order_by(AssessmentSubmission.submitted_at.desc())
        )
        submissions = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": sub.id,
                "assessment_id": sub.assessment_id,
                "assessment_title": sub.assessment.title if sub.assessment else "",
                "score": sub.score,
                "total_marks": sub.assessment.total_marks if sub.assessment else 100.0,
                "feedback": sub.feedback,
                "submitted_at": sub.submitted_at,
            }
            for sub in submissions
        ]

    @staticmethod
    async def record_attendance(
        db: AsyncSession,
        payload: AttendanceRecordCreate,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        await verify_faculty_section_access(payload.section_id, tenancy, db)

        async with transaction_scope(db):
            rec = StudentAttendanceRecord(
                id=str(uuid.uuid4()),
                campus_id=tenancy.campus_id,
                section_id=payload.section_id,
                student_id=payload.student_id,
                date=payload.date,
                status=payload.status,
                recorded_by=tenancy.user_id,
                recorded_at=utc_now(),
            )
            db.add(rec)
            await db.flush()

            # Recalculate attendance rate for student in this campus
            stmt = select(StudentAttendanceRecord.status).where(
                StudentAttendanceRecord.student_id == payload.student_id,
                StudentAttendanceRecord.campus_id == tenancy.campus_id,
            )
            all_statuses = (await db.execute(stmt)).scalars().all()
            if all_statuses:
                present_count = sum(1 for s in all_statuses if s in ("Present", "Late"))
                rate = round((present_count / len(all_statuses)) * 100.0, 1)
                stu_upd = (
                    select(Student)
                    .where(Student.id == payload.student_id, Student.campus_id == tenancy.campus_id)
                )
                student = (await db.execute(stu_upd)).scalar_one_or_none()
                if student:
                    student.attendance_rate = rate

        return {
            "id": rec.id,
            "status": "success",
            "attendance_rate": student.attendance_rate if student else None,
        }

    @staticmethod
    async def create_assessment(
        db: AsyncSession,
        payload: AssessmentCreate,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        await verify_faculty_section_access(payload.section_id, tenancy, db)

        async with transaction_scope(db):
            ass = Assessment(
                id=str(uuid.uuid4()),
                campus_id=tenancy.campus_id,
                section_id=payload.section_id,
                title=payload.title,
                assessment_type=payload.assessment_type,
                total_marks=payload.total_marks,
                clo_code=payload.clo_code,
                due_at=payload.due_at,
                created_by=tenancy.user_id,
                created_at=utc_now(),
            )
            db.add(ass)

        return {
            "id": ass.id,
            "section_id": ass.section_id,
            "title": ass.title,
            "total_marks": ass.total_marks,
        }

    @staticmethod
    async def enter_marks(
        db: AsyncSession,
        payload: MarkEntry,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        # Fetch assessment and verify section taught by faculty
        ass_stmt = (
            select(Assessment)
            .join(CourseSection, CourseSection.id == Assessment.section_id)
            .where(
                Assessment.id == payload.assessment_id,
                Assessment.campus_id == tenancy.campus_id,
                CourseSection.faculty_id == tenancy.user_id,
            )
        )
        ass = (await db.execute(ass_stmt)).scalar_one_or_none()
        if not ass:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not manage this assessment.",
            )

        async with transaction_scope(db):
            # Check for existing submission
            sub_stmt = select(AssessmentSubmission).where(
                AssessmentSubmission.assessment_id == payload.assessment_id,
                AssessmentSubmission.student_id == payload.student_id,
            )
            sub = (await db.execute(sub_stmt)).scalar_one_or_none()
            now = utc_now()
            if sub:
                sub.score = payload.score
                sub.feedback = payload.feedback
                sub.graded_by = tenancy.user_id
            else:
                sub = AssessmentSubmission(
                    id=str(uuid.uuid4()),
                    campus_id=tenancy.campus_id,
                    assessment_id=payload.assessment_id,
                    student_id=payload.student_id,
                    score=payload.score,
                    feedback=payload.feedback,
                    graded_by=tenancy.user_id,
                    submitted_at=now,
                )
                db.add(sub)
            await db.flush()

            # Recalculate average quiz score
            scores_stmt = select(AssessmentSubmission.score).where(
                AssessmentSubmission.student_id == payload.student_id,
                AssessmentSubmission.campus_id == tenancy.campus_id,
            )
            scores = (await db.execute(scores_stmt)).scalars().all()
            if scores:
                avg_score = round(sum(scores) / len(scores), 1)
                student = (await db.execute(
                    select(Student).where(Student.id == payload.student_id, Student.campus_id == tenancy.campus_id)
                )).scalar_one_or_none()
                if student:
                    student.quiz_score_avg = avg_score

        return {"status": "success", "score": payload.score}

    @staticmethod
    async def get_gradebook(
        db: AsyncSession,
        section_id: str,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        await verify_faculty_section_access(section_id, tenancy, db)

        # Assessments in section
        ass_stmt = (
            select(Assessment)
            .where(Assessment.section_id == section_id, Assessment.campus_id == tenancy.campus_id)
            .order_by(Assessment.created_at.asc())
        )
        assessments = (await db.execute(ass_stmt)).scalars().all()

        # Students in section
        stu_stmt = (
            select(Student)
            .join(CourseEnrollment, CourseEnrollment.student_id == Student.id)
            .where(CourseEnrollment.section_id == section_id, CourseEnrollment.campus_id == tenancy.campus_id)
        )
        students = (await db.execute(stu_stmt)).scalars().all()

        # All submissions for these assessments
        ass_ids = [a.id for a in assessments]
        submissions_map: Dict[str, Dict[str, float]] = {}
        if ass_ids:
            sub_stmt = select(AssessmentSubmission).where(
                AssessmentSubmission.assessment_id.in_(ass_ids),
                AssessmentSubmission.campus_id == tenancy.campus_id,
            )
            subs = (await db.execute(sub_stmt)).scalars().all()
            for s in subs:
                submissions_map.setdefault(s.student_id, {})[s.assessment_id] = s.score

        rows = []
        for st in students:
            scores = submissions_map.get(st.id, {})
            rows.append({
                "student_id": st.id,
                "student_name": st.full_name,
                "student_uid": st.student_uid,
                "scores": scores,
                "average": st.quiz_score_avg,
            })

        return {
            "section_id": section_id,
            "assessments": [{"id": a.id, "title": a.title, "total_marks": a.total_marks} for a in assessments],
            "gradebook": rows,
        }

    @staticmethod
    async def get_observations(
        db: AsyncSession,
        student_id: str,
        tenancy: TenancyContext,
    ) -> List[Dict[str, Any]]:
        await verify_faculty_student_access(student_id, tenancy, db)

        stmt = (
            select(Observation)
            .where(
                Observation.student_id == student_id,
                Observation.campus_id == tenancy.campus_id,
            )
            .order_by(Observation.created_at.desc())
        )
        obs = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": o.id,
                "domain": o.domain,
                "source": o.source,
                "data": o.data,
                "metric_key": "attendance_rate" if o.domain == "attendance" else o.domain,
                "observed_at": o.observed_at,
            }
            for o in obs
        ]

    @staticmethod
    async def evaluate_student_signal(
        db: AsyncSession,
        student_id: str,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        student = await verify_faculty_student_access(student_id, tenancy, db)

        # Deterministic evaluation logic
        attention_suggested = False
        reasons = []
        if student.attendance_rate < 75.0:
            attention_suggested = True
            reasons.append(f"Attendance rate ({student.attendance_rate}%) is below 75% threshold.")
        if student.quiz_score_avg < 60.0:
            attention_suggested = True
            reasons.append(f"Quiz score average ({student.quiz_score_avg}%) is below 60% threshold.")

        result = "attention_suggested" if attention_suggested else "no_rule_triggered"
        evidence_snapshot = {
            "attendance_rate": student.attendance_rate,
            "quiz_score_avg": student.quiz_score_avg,
            "reasons": reasons,
            "evaluated_at": utc_now().isoformat(),
        }
        digest = compute_sha256(evidence_snapshot)

        async with transaction_scope(db):
            signal = Signal(
                id=str(uuid.uuid4()),
                campus_id=tenancy.campus_id,
                student_id=student.id,
                rule_key="ATTENDANCE_AND_ACADEMIC_RISK",
                result=result,
                ml_risk_probability=0.82 if attention_suggested else 0.15,
                ml_tier="HIGH" if student.attendance_rate < 70.0 else ("MEDIUM" if attention_suggested else "WATCH"),
                evidence_snapshot=json.dumps(evidence_snapshot),
                created_at=utc_now(),
            )
            db.add(signal)

        return {
            "signal_id": signal.id,
            "result": result,
            "evidence_digest": digest,
            "ml_tier": signal.ml_tier,
        }

    @staticmethod
    async def list_signals(db: AsyncSession, tenancy: TenancyContext) -> List[Dict[str, Any]]:
        # Signals for students enrolled in faculty sections
        sec_stmt = select(CourseSection.id).where(
            CourseSection.faculty_id == tenancy.user_id,
            CourseSection.campus_id == tenancy.campus_id,
        )
        sec_ids = (await db.execute(sec_stmt)).scalars().all()

        if not sec_ids:
            return []

        stmt = (
            select(Signal)
            .join(CourseEnrollment, CourseEnrollment.student_id == Signal.student_id)
            .where(
                CourseEnrollment.section_id.in_(sec_ids),
                Signal.campus_id == tenancy.campus_id,
                Signal.reviewed == False,  # noqa: E712
            )
            .order_by(Signal.created_at.desc())
        )
        signals = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": sig.id,
                "student_id": sig.student_id,
                "rule_key": sig.rule_key,
                "result": sig.result,
                "ml_tier": sig.ml_tier,
                "ml_risk_probability": sig.ml_risk_probability,
                "created_at": sig.created_at,
            }
            for sig in signals
        ]

    @staticmethod
    async def review_signal(
        db: AsyncSession,
        signal_id: str,
        payload: SignalReviewRequest,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        stmt = select(Signal).where(Signal.id == signal_id, Signal.campus_id == tenancy.campus_id)
        sig = (await db.execute(stmt)).scalar_one_or_none()
        if not sig:
            raise EntityNotFoundError("Signal", signal_id)

        # Verify faculty student access
        await verify_faculty_student_access(sig.student_id, tenancy, db)

        case_id = None
        now = utc_now()
        async with transaction_scope(db):
            sig.reviewed = True
            sig.reviewed_decision = payload.decision
            sig.review_reason = payload.reason
            sig.reviewed_by = tenancy.user_id
            sig.reviewed_at = now

            if payload.decision == "approve":
                # Create academic case via Case model
                case_id = str(uuid.uuid4())
                case = Case(
                    id=case_id,
                    campus_id=tenancy.campus_id,
                    student_id=sig.student_id,
                    assigned_counsellor_id=tenancy.user_id,
                    originating_signal_id=sig.id,
                    status=CaseState.ACTION_PLANNED.value,
                    priority="high",
                    title=f"Academic Intervention — {payload.selected_intervention_key or 'Support'}",
                    description=payload.reason or "Approved from automated academic signal review.",
                    due_date=now + timedelta(days=7),
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
                db.add(case)
                await db.flush()

                # Add CaseEvent
                event = CaseEvent(
                    id=str(uuid.uuid4()),
                    case_id=case.id,
                    actor_id=tenancy.user_id,
                    campus_id=tenancy.campus_id,
                    event_type="SIGNAL_APPROVED_CASE_CREATED",
                    payload={"signal_id": sig.id, "to_state": CaseState.ACTION_PLANNED.value},
                    created_at=now,
                )
                db.add(event)

                # Add AuditEvent
                audit = AuditEvent(
                    id=str(uuid.uuid4()),
                    actor_id=tenancy.user_id,
                    campus_id=tenancy.campus_id,
                    entity_type="case",
                    entity_id=case.id,
                    action="case.created_from_signal",
                    event_metadata={"signal_id": sig.id, "decision": "approve"},
                    correlation_id=str(uuid.uuid4()),
                    event_hash=compute_sha256({"case_id": case.id, "signal_id": sig.id}),
                    created_at=now,
                )
                db.add(audit)

        return {
            "signal_id": sig.id,
            "decision": payload.decision,
            "case_id": case_id,
            "status": "reviewed",
        }

    @staticmethod
    async def create_case_task(
        db: AsyncSession,
        case_id: str,
        payload: CaseTaskCreate,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        case = await CaseService.get_case(db, case_id, tenancy.campus_id, tenancy.is_platform_admin)
        await verify_faculty_student_access(case.student_id, tenancy, db)

        now = utc_now()
        async with transaction_scope(db):
            # Check or create catalogue item
            cat_stmt = select(InterventionCatalogue).where(
                InterventionCatalogue.name == payload.generic_label
            )
            cat = (await db.execute(cat_stmt)).scalar_one_or_none()
            if not cat:
                cat = InterventionCatalogue(
                    id=str(uuid.uuid4()),
                    name=payload.generic_label,
                    category=payload.domain,
                    description=payload.generic_label,
                    is_active=True,
                    created_at=now,
                )
                db.add(cat)
                await db.flush()

            task_id = str(uuid.uuid4())
            interv = Intervention(
                id=task_id,
                case_id=case.id,
                catalogue_id=cat.id,
                counsellor_id=tenancy.user_id,
                campus_id=tenancy.campus_id,
                description=payload.generic_label,
                start_date=now,
                target_date=now + timedelta(days=payload.due_days or 3),
                progress="in_progress",
                created_at=now,
                updated_at=now,
            )
            db.add(interv)

            # Audit event with SHA-256 hash
            audit_hash = compute_sha256({"case_id": case.id, "task_id": task_id, "label": payload.generic_label})
            audit = AuditEvent(
                id=str(uuid.uuid4()),
                actor_id=tenancy.user_id,
                campus_id=tenancy.campus_id,
                entity_type="case_task",
                entity_id=task_id,
                action="task.created",
                event_metadata={"domain": payload.domain, "label": payload.generic_label},
                event_hash=audit_hash,
                created_at=now,
            )
            db.add(audit)

        return {"task_id": task_id, "audit_hash": audit_hash, "state": "created"}

    @staticmethod
    async def log_case_follow_up(
        db: AsyncSession,
        case_id: str,
        payload: FollowUpCreate,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        case = await CaseService.get_case(db, case_id, tenancy.campus_id, tenancy.is_platform_admin)
        await verify_faculty_student_access(case.student_id, tenancy, db)

        now = utc_now()
        async with transaction_scope(db):
            fu_id = str(uuid.uuid4())
            fu = FollowUp(
                id=fu_id,
                case_id=case.id,
                counsellor_id=tenancy.user_id,
                campus_id=tenancy.campus_id,
                title=f"{payload.follow_up_type}: {payload.contact_status}",
                description=payload.sanitized_note,
                scheduled_at=now,
                status="completed",
                completed_at=now,
                completed_by=tenancy.user_id,
                created_at=now,
                updated_at=now,
            )
            db.add(fu)

            # Transition case status to support_in_progress if in action_planned or assigned
            case.status = CaseState.SUPPORT_IN_PROGRESS.value
            case.updated_at = now
            case.version += 1

            audit = AuditEvent(
                id=str(uuid.uuid4()),
                actor_id=tenancy.user_id,
                campus_id=tenancy.campus_id,
                entity_type="case_followup",
                entity_id=fu_id,
                action="followup.logged",
                event_metadata={"type": payload.follow_up_type, "note": payload.sanitized_note},
                event_hash=compute_sha256({"case_id": case.id, "fu_id": fu_id}),
                created_at=now,
            )
            db.add(audit)

        return {"followup_id": fu_id, "case_state": case.status}

    @staticmethod
    async def escalate_case(
        db: AsyncSession,
        case_id: str,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        case = await CaseService.get_case(db, case_id, tenancy.campus_id, tenancy.is_platform_admin)
        await verify_faculty_student_access(case.student_id, tenancy, db)

        now = utc_now()
        async with transaction_scope(db):
            case.priority = "urgent"
            case.version += 1
            case.updated_at = now

            audit_hash = compute_sha256({"case_id": case.id, "action": "case.escalated", "version": case.version})
            audit = AuditEvent(
                id=str(uuid.uuid4()),
                actor_id=tenancy.user_id,
                campus_id=tenancy.campus_id,
                entity_type="case",
                entity_id=case.id,
                action="case.escalated",
                event_metadata={"priority": "urgent", "escalated_by": tenancy.user_id},
                event_hash=audit_hash,
                created_at=now,
            )
            db.add(audit)

        return {"case_id": case.id, "status": "escalated", "audit_hash": audit_hash}

    @staticmethod
    async def record_case_outcome(
        db: AsyncSession,
        case_id: str,
        payload: CaseOutcomeCreate,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        case = await CaseService.get_case(db, case_id, tenancy.campus_id, tenancy.is_platform_admin)
        await verify_faculty_student_access(case.student_id, tenancy, db)

        now = utc_now()
        async with transaction_scope(db):
            case.status = CaseState.CLOSED.value
            case.closed_at = now
            case.closed_by = tenancy.user_id
            case.version += 1
            case.updated_at = now

            audit_hash = compute_sha256({"case_id": case.id, "outcome": payload.outcome_status, "rationale": payload.rationale})
            audit = AuditEvent(
                id=str(uuid.uuid4()),
                actor_id=tenancy.user_id,
                campus_id=tenancy.campus_id,
                entity_type="case",
                entity_id=case.id,
                action="case.closed_with_outcome",
                event_metadata={"outcome": payload.outcome_status, "rationale": payload.rationale},
                event_hash=audit_hash,
                created_at=now,
            )
            db.add(audit)

        return {"case_id": case.id, "state": "closed", "audit_hash": audit_hash}

    @staticmethod
    async def get_case_audit_history(
        db: AsyncSession,
        case_id: str,
        tenancy: TenancyContext,
    ) -> List[Dict[str, Any]]:
        case = await CaseService.get_case(db, case_id, tenancy.campus_id, tenancy.is_platform_admin)
        await verify_faculty_student_access(case.student_id, tenancy, db)

        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.campus_id == tenancy.campus_id,
                AuditEvent.entity_id == case.id,
            )
            .order_by(AuditEvent.created_at.asc())
        )
        events = (await db.execute(stmt)).scalars().all()
        # Also include any task or followup audit events for this case
        return [
            {
                "id": ev.id,
                "actor_id": ev.actor_id,
                "action": ev.action,
                "metadata": ev.event_metadata,
                "hash": ev.event_hash or compute_sha256({"id": ev.id, "action": ev.action}),
                "created_at": ev.created_at,
            }
            for ev in events
        ]
