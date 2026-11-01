from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_tenancy_context, require_role, TenancyContext
from app.core.permissions import Role
from app.modules.faculty.services import FacultyService
from app.modules.cases.services import CaseService, case_to_detail_response
from app.modules.cases.schemas import CaseDetailResponse
from app.modules.faculty.schemas import (
    AttendanceRecordCreate,
    AssessmentCreate,
    MarkEntry,
    SignalReviewRequest,
    CaseTaskCreate,
    FollowUpCreate,
    CaseOutcomeCreate,
)

router = APIRouter()


@router.get("/dashboard")
async def get_faculty_dashboard(
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_dashboard(db, tenancy)


@router.get("/courses")
async def get_faculty_courses(
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.list_courses(db, tenancy)


@router.get("/sections")
async def get_faculty_sections(
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.list_sections(db, tenancy)


@router.get("/sections/{section_id}/students")
async def get_section_students(
    section_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_section_students(db, section_id, tenancy)


@router.get("/students/{student_id}")
async def get_student_detail(
    student_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_student_detail(db, student_id, tenancy)


@router.get("/students/{student_id}/attendance")
async def get_student_attendance(
    student_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_student_attendance(db, student_id, tenancy)


@router.get("/students/{student_id}/academics")
async def get_student_academics(
    student_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_student_academics(db, student_id, tenancy)


@router.post("/attendance")
async def record_attendance(
    payload: AttendanceRecordCreate,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.record_attendance(db, payload, tenancy)


@router.post("/assessments", status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.create_assessment(db, payload, tenancy)


@router.post("/marks")
async def enter_marks(
    payload: MarkEntry,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.enter_marks(db, payload, tenancy)


@router.get("/gradebook/{section_id}")
async def get_gradebook(
    section_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_gradebook(db, section_id, tenancy)


@router.get("/students/{student_id}/observations")
async def get_student_observations(
    student_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_observations(db, student_id, tenancy)


@router.post("/students/{student_id}/signals/evaluate", status_code=status.HTTP_201_CREATED)
async def evaluate_student_signal(
    student_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.evaluate_student_signal(db, student_id, tenancy)


@router.get("/signals")
async def get_faculty_signals(
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.list_signals(db, tenancy)


@router.post("/signals/{signal_id}/review")
async def review_signal(
    signal_id: str,
    payload: SignalReviewRequest,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.review_signal(db, signal_id, payload, tenancy)


@router.get("/cases")
async def get_faculty_cases(
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    cases = await CaseService.list_cases(
        db=db,
        campus_id=tenancy.campus_id,
        actor_id=tenancy.user_id,
        actor_roles=[tenancy.role.value],
        is_platform_admin=tenancy.is_platform_admin,
    )
    return [case_to_detail_response(c) for c in cases]


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_case_detail(
    case_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    case = await CaseService.get_case(db, case_id, tenancy.campus_id, tenancy.is_platform_admin)
    visible = await CaseService.list_cases(
        db=db, campus_id=tenancy.campus_id, actor_id=tenancy.user_id, actor_roles=[tenancy.role.value],
        is_platform_admin=tenancy.is_platform_admin, student_id=case.student_id, limit=1,
    )
    if not visible:
        raise HTTPException(status_code=403, detail="This student is not in one of your sections")
    return case_to_detail_response(case)


@router.post("/cases/{case_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_case_task(
    case_id: str,
    payload: CaseTaskCreate,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.create_case_task(db, case_id, payload, tenancy)


@router.post("/cases/{case_id}/follow-ups")
async def log_case_follow_up(
    case_id: str,
    payload: FollowUpCreate,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.log_case_follow_up(db, case_id, payload, tenancy)


@router.post("/cases/{case_id}/escalate")
async def escalate_case(
    case_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.escalate_case(db, case_id, tenancy)


@router.post("/cases/{case_id}/outcome")
async def record_case_outcome(
    case_id: str,
    payload: CaseOutcomeCreate,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.record_case_outcome(db, case_id, payload, tenancy)


@router.get("/cases/{case_id}/history")
async def get_case_audit_history(
    case_id: str,
    tenancy: TenancyContext = Depends(require_role(Role.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService.get_case_audit_history(db, case_id, tenancy)
