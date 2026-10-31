import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import Role
from app.services.counsellor_service import CounsellorService
from app.services.followup_service import FollowUpService
from app.schemas.counsellor import (
    CounsellorDashboardResponse,
    CounsellorDashboardSummary,
    UpcomingFollowUpItem,
    OverdueCaseItem,
    CounsellorProfileResponse,
    CounsellorProfileUpdateRequest,
    StudentListItem,
    StudentDetailResponse,
    StudentObservationItem,
    StudentSupportHistoryItem
)
from app.schemas.followups import FollowUpResponse
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/counsellor", tags=["Counsellor Module"])

# Common dependency ensuring only authorized counsellors can access these routes
require_counsellor = require_roles(Role.COUNSELLOR, Role.INSTITUTION_ADMIN)

# --- MODULE A: DASHBOARD ---

@router.get("/dashboard", response_model=CounsellorDashboardResponse)
async def get_dashboard(current_user: dict = Depends(require_counsellor)):
    """C01-C07: Complete aggregated dashboard view for the authenticated counsellor."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CounsellorService.get_dashboard(counsellor_id, campus_id)

@router.get("/dashboard/summary", response_model=CounsellorDashboardSummary)
async def get_dashboard_summary(current_user: dict = Depends(require_counsellor)):
    """C01-C06: Numerical aggregated metrics for the counsellor's active workload."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    data = CounsellorService.get_dashboard(counsellor_id, campus_id)
    return data["summary"]

@router.get("/dashboard/upcoming-followups", response_model=List[UpcomingFollowUpItem])
async def get_upcoming_followups(current_user: dict = Depends(require_counsellor)):
    """C07: Chronological list of upcoming follow-ups requiring counsellor action."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    data = CounsellorService.get_dashboard(counsellor_id, campus_id)
    return data["upcoming_followups"]

@router.get("/dashboard/overdue-cases", response_model=List[OverdueCaseItem])
async def get_overdue_cases(current_user: dict = Depends(require_counsellor)):
    """C06: Cases whose resolution deadline has lapsed and require immediate intervention."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    data = CounsellorService.get_dashboard(counsellor_id, campus_id)
    return data["overdue_cases"]

# --- MODULE G: PROFILE MANAGEMENT ---

@router.get("/profile", response_model=CounsellorProfileResponse)
async def get_profile(current_user: dict = Depends(require_counsellor)):
    """C69: Retrieve detailed profile and qualifications for authenticated counsellor."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CounsellorService.get_profile(counsellor_id, campus_id)

@router.patch("/profile", response_model=CounsellorProfileResponse)
async def update_profile(
    payload: CounsellorProfileUpdateRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C70: Update permitted profile fields. Roles and campus cannot be modified."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    dump_kwargs = {"exclude_unset": True}
    data = payload.model_dump(**dump_kwargs) if hasattr(payload, "model_dump") else payload.dict(**dump_kwargs)
    return CounsellorService.update_profile(counsellor_id, campus_id, data)

# --- MODULE B: STUDENT VISIBILITY ---

@router.get("/students", response_model=PaginatedResponse[StudentListItem])
async def list_assigned_students(
    search: Optional[str] = Query(None, description="Search by name or external student ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_counsellor)
):
    """C11-C12: View and search students within the counsellor's authorized scope."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    items, total = CounsellorService.list_assigned_students(
        counsellor_id, campus_id, search=search, page=page, page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/students/{student_id}", response_model=StudentDetailResponse)
async def get_student_detail(
    student_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C14: Authorized student profile overview, course enrolment, and assigned cases."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CounsellorService.get_student_detail(student_id, counsellor_id, campus_id)

@router.get("/students/{student_id}/observations", response_model=List[StudentObservationItem])
async def get_student_observations(
    student_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C20: View academic & attendance observations relevant to student's cases."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CounsellorService.get_student_observations(student_id, counsellor_id, campus_id)

@router.get("/students/{student_id}/support-history", response_model=List[StudentSupportHistoryItem])
async def get_student_support_history(
    student_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C17: Review full institutional support history, previous cases and outcomes."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CounsellorService.get_student_support_history(student_id, counsellor_id, campus_id)

# --- MODULE E: COUNSELLOR FOLLOW-UPS LISTING ---

@router.get("/followups", response_model=PaginatedResponse[FollowUpResponse])
async def list_counsellor_followups(
    upcoming_only: bool = Query(True, description="Filter for pending scheduled follow-ups"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_counsellor)
):
    """C41: View scheduled upcoming follow-ups across all assigned cases."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    items, total = FollowUpService.list_counsellor_followups(
        counsellor_id, campus_id, upcoming_only=upcoming_only, page=page, page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/followups/history", response_model=PaginatedResponse[FollowUpResponse])
async def get_followup_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_counsellor)
):
    """C47: Historical follow-up tracking log (completed, missed, rescheduled)."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    items, total = FollowUpService.get_followup_history(
        counsellor_id, campus_id, page=page, page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
