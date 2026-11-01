from typing import Optional, List, Set
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token
from app.core.permissions import Role, Action, ACTION_PERMISSIONS
from app.core.database import get_db
from app.modules.identity.models import User, Membership

security_scheme = HTTPBearer(auto_error=False)

# Default role when a user holds several on one campus and sends no X-Role
ROLE_PRIORITY = ["institution_admin", "hod", "counsellor", "faculty", "mentor", "student"]


class TenancyContext:
    """Encapsulates the trusted, database-verified identity, campus tenancy, and role context."""

    def __init__(
        self,
        user_id: str,
        email: str,
        campus_id: str,
        role: Role,
        is_platform_admin: bool = False,
        membership_id: Optional[str] = None,
        department: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.campus_id = campus_id
        self.role = role
        self.is_platform_admin = is_platform_admin
        self.membership_id = membership_id
        self.department = department

    def has_role(self, *roles: Role) -> bool:
        return self.role in roles


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    """Extract and authenticate the bearer token, returning the decoded user payload.

    Raises HTTP 401 Unauthorized for missing, invalid, expired, or tampered tokens.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_tenancy_context(
    x_campus_id: Optional[str] = Header(None, alias="X-Campus-ID"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenancyContext:
    """Validate caller identity and active campus membership from the database.

    Enforces that:
    1. The authenticated user exists and is active.
    2. The caller has an active membership in the requested campus (or platform admin privileges).
    3. Revoked roles or deactivated memberships take effect immediately on every request.
    """
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject identifier",
        )

    # 1. Verify user is active in the database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or has been deactivated",
        )

    # 2. Check for Platform Admin privilege (global override). Memberships arrive with the user (selectin).
    active = [m for m in user.memberships if m.is_active]
    platform_membership = next((m for m in active if m.role == Role.PLATFORM_ADMIN.value), None)
    if platform_membership:
        campus_id = x_campus_id or "platform-global"
        return TenancyContext(
            user_id=user.id,
            email=user.email,
            campus_id=campus_id,
            role=Role.PLATFORM_ADMIN,
            is_platform_admin=True,
            membership_id=platform_membership.id,
        )

    # 3. For institutional/campus users, campus ID is mandatory
    campus_id = x_campus_id or current_user.get("campus_id")
    if not campus_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing campus tenancy identifier (X-Campus-ID header required)",
        )

    # 4. Verify active membership in the specified campus
    in_campus = [m for m in active if m.campus_id == campus_id]
    membership = None
    if x_role:  # the caller picks one of the roles they genuinely hold on this campus
        membership = next((m for m in in_campus if m.role == x_role), None)
        if not membership and in_campus:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not hold the role '{x_role}' on this campus")
    elif in_campus:
        membership = min(in_campus, key=lambda m: ROLE_PRIORITY.index(m.role) if m.role in ROLE_PRIORITY else 99)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: No active membership found for campus '{campus_id}'",
        )

    try:
        role = Role(membership.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Unrecognised role '{membership.role}' assigned",
        )

    return TenancyContext(
        user_id=user.id,
        email=user.email,
        campus_id=campus_id,
        role=role,
        is_platform_admin=False,
        membership_id=membership.id,
        department=membership.department,
    )


def require_role(*roles: Role):
    """Enforce that the caller's active campus role matches one of the authorized roles."""
    def role_checker(tenancy: TenancyContext = Depends(get_tenancy_context)) -> TenancyContext:
        if tenancy.role not in roles and not tenancy.is_platform_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Operation requires one of {[r.value for r in roles]}",
            )
        return tenancy

    return role_checker


def require_permission(action: Action):
    """Enforce that the caller's active campus role is authorized for the requested domain action."""
    def permission_checker(tenancy: TenancyContext = Depends(get_tenancy_context)) -> TenancyContext:
        allowed_roles = ACTION_PERMISSIONS.get(action, set())
        if tenancy.role not in allowed_roles and not tenancy.is_platform_admin:
            # Explicit clear rejection for Admins attempting clinical counselling records
            if (
                action in (Action.VIEW_CONFIDENTIAL_NOTES, Action.CREATE_CONFIDENTIAL_NOTES)
                and tenancy.role == Role.INSTITUTION_ADMIN
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Institution Admins do not have access to confidential counselling notes",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{tenancy.role.value}' does not have permission for '{action.value}'",
            )
        return tenancy

    return permission_checker


def verify_resource_access(
    tenancy: TenancyContext,
    resource_campus_id: str,
    assigned_counsellor_id: Optional[str] = None,
    is_confidential: bool = False,
    for_update: bool = False,
) -> None:
    """Validate campus data isolation and object-level permissions on specific domain resources."""
    # 1. Enforce strict campus data isolation
    if resource_campus_id != tenancy.campus_id and not tenancy.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found in the active campus",
        )

    # 2. Enforce confidential clinical notes boundary
    if is_confidential:
        if tenancy.role != Role.COUNSELLOR and not tenancy.is_platform_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Confidential counselling notes are restricted to authorised counselling staff",
            )
        if (
            assigned_counsellor_id
            and assigned_counsellor_id != tenancy.user_id
            and not tenancy.is_platform_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Counsellor is not assigned to this confidential record",
            )

    # 3. Enforce mutation scope boundaries
    if for_update:
        if tenancy.role == Role.COUNSELLOR:
            if assigned_counsellor_id and assigned_counsellor_id != tenancy.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Only the assigned counsellor may modify this case",
                )
        elif tenancy.role == Role.INSTITUTION_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Institution Admins have supervisory oversight and cannot modify active counselling workflows directly",
            )


async def verify_faculty_section_access(
    section_id: str,
    tenancy: TenancyContext,
    db: AsyncSession,
):
    from app.modules.faculty.models import CourseSection
    stmt = select(CourseSection).where(
        CourseSection.id == section_id,
        CourseSection.campus_id == tenancy.campus_id,
    )
    if not tenancy.is_platform_admin:
        stmt = stmt.where(CourseSection.faculty_id == tenancy.user_id)
    res = await db.execute(stmt)
    section = res.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to view or manage this section.",
        )
    return section


async def verify_faculty_student_access(
    student_id: str,
    tenancy: TenancyContext,
    db: AsyncSession,
):
    from app.modules.roster.models import Student
    from app.modules.faculty.models import CourseSection, CourseEnrollment
    if tenancy.is_platform_admin:
        stmt = select(Student).where(Student.id == student_id, Student.campus_id == tenancy.campus_id)
    else:
        stmt = (
            select(Student)
            .join(CourseEnrollment, CourseEnrollment.student_id == Student.id)
            .join(CourseSection, CourseSection.id == CourseEnrollment.section_id)
            .where(
                Student.id == student_id,
                CourseSection.faculty_id == tenancy.user_id,
                CourseSection.campus_id == tenancy.campus_id,
            )
        )
    res = await db.execute(stmt)
    student = res.scalars().first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Student is not enrolled in any of your assigned courses.",
        )
    return student

async def get_current_student(
    tenancy: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.roster.models import Student
    stmt = select(Student).where(
        Student.user_id == tenancy.user_id,
        Student.campus_id == tenancy.campus_id,
    )
    res = await db.execute(stmt)
    student = res.scalar_one_or_none()
    if not student and tenancy.email:
        stmt = select(Student).where(
            Student.email == tenancy.email,
            Student.campus_id == tenancy.campus_id,
        )
        res = await db.execute(stmt)
        student = res.scalar_one_or_none()
        if student and not student.user_id:
            student.user_id = tenancy.user_id
            await db.commit()

    if not student and tenancy.role == Role.STUDENT:
        from app.modules.identity.models import User
        user = await db.scalar(select(User).where(User.id == tenancy.user_id))
        full_name = user.full_name if user else (tenancy.email.split("@")[0].title() if tenancy.email else "Student")
        student = Student(
            campus_id=tenancy.campus_id,
            user_id=tenancy.user_id,
            student_uid=f"STU-{tenancy.user_id[:8].upper()}",
            full_name=full_name,
            email=tenancy.email,
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

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for active user in this campus",
        )
    return student
