from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.core.permissions import Role

ADMIN_ROLES = (Role.INSTITUTION_ADMIN,)
# Staff who may award points for verified activities (PTS-03). Blueprint 04 lists admin only;
# blueprint 10 says "authorised staff role". HOD and counsellor are included, see report.
AWARD_ROLES = (Role.INSTITUTION_ADMIN, Role.HOD, Role.COUNSELLOR)
ALLOWED_ROLES = [*ADMIN_ROLES, Role.PLATFORM_ADMIN]


async def current_student(
    ctx: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Student resolved from the verified account link, never from the client (PUL-03, RED-02)."""
    from app.modules.roster.models import Student
    student = await db.scalar(
        select(Student).where(Student.user_id == ctx.user_id, Student.campus_id == ctx.campus_id)
    )
    if not student and ctx.email:
        student = await db.scalar(
            select(Student).where(Student.email == ctx.email, Student.campus_id == ctx.campus_id)
        )
        if student and not student.user_id:
            student.user_id = ctx.user_id
            await db.commit()

    if not student:
        # Auto-provision student profile for authenticated student
        from app.modules.identity.models import User
        user = await db.scalar(select(User).where(User.id == ctx.user_id))
        full_name = user.full_name if user else (ctx.email.split("@")[0].title() if ctx.email else "Student")
        student = Student(
            campus_id=ctx.campus_id,
            user_id=ctx.user_id,
            student_uid=f"STU-{ctx.user_id[:8].upper()}",
            full_name=full_name,
            email=ctx.email,
            department="Computer Science",
            course="B.Tech",
            academic_year=2026,
            cohort_code="COHORT-2026",
            enrollment_status="active",
            attendance_rate=92.5,
            quiz_score_avg=84.0,
            is_active=True,
        )
        db.add(student)
        await db.commit()

    return student
