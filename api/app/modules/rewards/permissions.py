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
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student profile not found for active user in this campus")
    return student
