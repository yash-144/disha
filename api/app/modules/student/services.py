import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.shared.utils import utc_now
from app.core.exceptions import EntityNotFoundError
from app.core.dependencies import TenancyContext
from app.modules.roster.models import Student
from app.modules.faculty.models import (
    Course,
    CourseSection,
    CourseEnrollment,
    StudentAttendanceRecord,
    Assessment,
    AssessmentSubmission,
)
from app.modules.student.models import SupportRequest
from app.modules.notifications.models import Notification
from app.modules.cases.services import transaction_scope
from app.modules.student.schemas import (
    SupportRequestCreate,
    SupportRequestResponse,
    StudentProfileResponse,
    StudentDashboardResponse,
)


class StudentService:

    @staticmethod
    async def _get_current_student(db: AsyncSession, tenancy: TenancyContext) -> Student:
        stmt = select(Student).where(
            Student.user_id == tenancy.user_id,
            Student.campus_id == tenancy.campus_id,
        )
        student = (await db.execute(stmt)).scalar_one_or_none()
        if not student:
            # Fallback check if student ID matches user_id directly or first active record
            stmt2 = select(Student).where(
                Student.id == tenancy.user_id,
                Student.campus_id == tenancy.campus_id,
            )
            student = (await db.execute(stmt2)).scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found for active user in this campus",
            )
        return student

    @staticmethod
    async def get_dashboard(db: AsyncSession, tenancy: TenancyContext) -> Dict[str, Any]:
        student = await StudentService._get_current_student(db, tenancy)

        # Enrolled courses
        stmt = (
            select(CourseSection)
            .join(CourseEnrollment, CourseEnrollment.section_id == CourseSection.id)
            .options(selectinload(CourseSection.course))
            .where(
                CourseEnrollment.student_id == student.id,
                CourseEnrollment.campus_id == tenancy.campus_id,
            )
        )
        sections = (await db.execute(stmt)).scalars().all()

        courses_data = [
            {
                "section_id": s.id,
                "course_id": s.course_id,
                "course_title": s.course.title if s.course else "",
                "course_code": s.course.code if s.course else "",
                "section_code": s.section_code,
                "term": s.term,
                "color": s.color,
            }
            for s in sections
        ]

        return {
            "student_summary": {
                "id": student.id,
                "student_uid": student.student_uid,
                "display_name": student.full_name,
                "full_name": student.full_name,
                "email": student.email,
                "department": student.department,
                "cohort_code": student.cohort_code,
            },
            "courses": courses_data,
            "attendance_rate": student.attendance_rate,
            "quiz_score_avg": student.quiz_score_avg,
        }

    @staticmethod
    async def get_profile(db: AsyncSession, tenancy: TenancyContext) -> Dict[str, Any]:
        student = await StudentService._get_current_student(db, tenancy)
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
    async def get_attendance(db: AsyncSession, tenancy: TenancyContext) -> Dict[str, Any]:
        student = await StudentService._get_current_student(db, tenancy)

        stmt = (
            select(StudentAttendanceRecord)
            .where(
                StudentAttendanceRecord.student_id == student.id,
                StudentAttendanceRecord.campus_id == tenancy.campus_id,
            )
            .order_by(StudentAttendanceRecord.date.desc())
        )
        records = (await db.execute(stmt)).scalars().all()
        return {
            "attendance_rate": student.attendance_rate,
            "records": [
                {
                    "id": r.id,
                    "section_id": r.section_id,
                    "date": r.date,
                    "status": r.status,
                    "recorded_at": r.recorded_at,
                }
                for r in records
            ],
        }

    @staticmethod
    async def get_academics(db: AsyncSession, tenancy: TenancyContext) -> Dict[str, Any]:
        student = await StudentService._get_current_student(db, tenancy)

        stmt = (
            select(AssessmentSubmission)
            .options(selectinload(AssessmentSubmission.assessment))
            .where(
                AssessmentSubmission.student_id == student.id,
                AssessmentSubmission.campus_id == tenancy.campus_id,
            )
            .order_by(AssessmentSubmission.submitted_at.desc())
        )
        submissions = (await db.execute(stmt)).scalars().all()
        return {
            "quiz_score_avg": student.quiz_score_avg,
            "submissions": [
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
            ],
        }

    @staticmethod
    async def get_courses(db: AsyncSession, tenancy: TenancyContext) -> List[Dict[str, Any]]:
        student = await StudentService._get_current_student(db, tenancy)

        stmt = (
            select(CourseSection)
            .join(CourseEnrollment, CourseEnrollment.section_id == CourseSection.id)
            .options(selectinload(CourseSection.course))
            .where(
                CourseEnrollment.student_id == student.id,
                CourseEnrollment.campus_id == tenancy.campus_id,
            )
        )
        sections = (await db.execute(stmt)).scalars().all()
        return [
            {
                "section_id": s.id,
                "course_id": s.course_id,
                "course_title": s.course.title if s.course else "",
                "course_code": s.course.code if s.course else "",
                "section_code": s.section_code,
                "term": s.term,
                "access_code": s.access_code,
                "color": s.color,
            }
            for s in sections
        ]

    @staticmethod
    async def get_assessments(db: AsyncSession, tenancy: TenancyContext) -> List[Dict[str, Any]]:
        student = await StudentService._get_current_student(db, tenancy)

        # Get all assessments in enrolled sections
        stmt = (
            select(Assessment)
            .join(CourseSection, CourseSection.id == Assessment.section_id)
            .join(CourseEnrollment, CourseEnrollment.section_id == CourseSection.id)
            .options(selectinload(Assessment.section))
            .where(
                CourseEnrollment.student_id == student.id,
                CourseEnrollment.campus_id == tenancy.campus_id,
            )
            .order_by(Assessment.due_at.asc())
        )
        assessments = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": a.id,
                "section_id": a.section_id,
                "section_name": a.section.name if a.section else "",
                "title": a.title,
                "assessment_type": a.assessment_type,
                "total_marks": a.total_marks,
                "due_at": a.due_at,
            }
            for a in assessments
        ]

    @staticmethod
    async def list_support_requests(db: AsyncSession, tenancy: TenancyContext) -> List[Dict[str, Any]]:
        student = await StudentService._get_current_student(db, tenancy)

        stmt = (
            select(SupportRequest)
            .where(
                SupportRequest.student_id == student.id,
                SupportRequest.campus_id == tenancy.campus_id,
            )
            .order_by(SupportRequest.created_at.desc())
        )
        requests = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": sr.id,
                "faculty_id": sr.faculty_id,
                "course_id": sr.course_id,
                "category": sr.category,
                "preferred_slot": sr.preferred_slot,
                "student_note": sr.student_note,
                "status": sr.status,
                "faculty_response": sr.faculty_response,
                "created_at": sr.created_at,
            }
            for sr in requests
        ]

    @staticmethod
    async def create_support_request(
        db: AsyncSession,
        payload: SupportRequestCreate,
        tenancy: TenancyContext,
    ) -> Dict[str, Any]:
        student = await StudentService._get_current_student(db, tenancy)

        faculty_id = payload.faculty_id
        if not faculty_id:
            from app.modules.faculty.models import CourseEnrollment, CourseSection
            row = await db.execute(
                select(CourseSection.faculty_id).join(CourseEnrollment, CourseEnrollment.section_id == CourseSection.id)
                .where(CourseEnrollment.student_id == student.id).limit(1)
            )
            faculty_id = row.scalar_one_or_none()
            if not faculty_id:
                raise HTTPException(status_code=422, detail="You are not enrolled in any course yet")

        now = utc_now()
        async with transaction_scope(db):
            req = SupportRequest(
                id=str(uuid.uuid4()),
                campus_id=tenancy.campus_id,
                student_id=student.id,
                faculty_id=faculty_id,
                course_id=payload.course_id,
                category=payload.category,
                preferred_slot=payload.preferred_slot,
                student_note=payload.student_note,
                status="requested",
                created_at=now,
                updated_at=now,
            )
            db.add(req)

        return {
            "id": req.id,
            "status": req.status,
            "category": req.category,
            "created_at": req.created_at,
        }

    @staticmethod
    async def get_notifications(db: AsyncSession, tenancy: TenancyContext) -> List[Dict[str, Any]]:
        stmt = (
            select(Notification)
            .where(
                Notification.recipient_id == tenancy.user_id,
                Notification.campus_id == tenancy.campus_id,
            )
            .order_by(Notification.created_at.desc())
        )
        notifs = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "notification_type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in notifs
        ]
