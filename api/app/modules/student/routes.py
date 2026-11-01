from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role, TenancyContext
from app.core.permissions import Role
from app.modules.student.services import StudentService
from app.modules.student.schemas import (
    SupportRequestCreate,
    SupportRequestResponse,
    StudentProfileResponse,
    StudentDashboardResponse,
)

router = APIRouter()


@router.get("/dashboard")
async def get_student_dashboard(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.get_dashboard(db, tenancy)


@router.get("/profile")
@router.get("/me")
async def get_student_profile(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.get_profile(db, tenancy)


@router.get("/attendance")
async def get_student_attendance(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.get_attendance(db, tenancy)


@router.get("/academics")
async def get_student_academics(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.get_academics(db, tenancy)


@router.get("/courses")
async def get_student_courses(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.get_courses(db, tenancy)


@router.get("/assessments")
async def get_student_assessments(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.get_assessments(db, tenancy)


@router.get("/support-requests")
async def get_student_support_requests(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.list_support_requests(db, tenancy)


@router.post("/support-requests", status_code=status.HTTP_201_CREATED)
async def create_support_request(
    payload: SupportRequestCreate,
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.create_support_request(db, payload, tenancy)


@router.get("/notifications")
async def get_student_notifications(
    tenancy: TenancyContext = Depends(require_role(Role.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentService.get_notifications(db, tenancy)
