from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import Role
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminDashboardSummary,
    CounsellorWorkloadMetric,
    UserItemResponse,
    UserListResponse,
    InviteStaffRequest,
    InvitationResponse,
    MembershipUpdateRequest,
    CampusDetailResponse,
    CampusUpdateRequest,
    AdminCaseListItem,
    AdminCaseDetail,
    ReassignCaseRequest,
    ImportJobResponse,
    AnalyticsOverviewResponse,
    AuditLogItemResponse,
    AdminProfileResponse,
    AdminProfileUpdateRequest,
    AdminChangePasswordRequest,
)

router = APIRouter(prefix="/admin", tags=["Admin Module"])

# Only institution_admin and platform_admin can access these endpoints
admin_auth = Depends(require_roles(Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN))

# ==========================================
# A. DASHBOARD ENDPOINTS
# ==========================================

@router.get("/dashboard", response_model=AdminDashboardSummary)
async def get_admin_dashboard(
    current_user: dict = admin_auth
):
    """A01-A10: Aggregated operational dashboard for campus administrators."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_dashboard_summary(campus_id)

@router.get("/dashboard/summary", response_model=AdminDashboardSummary)
async def get_dashboard_summary_alias(
    current_user: dict = admin_auth
):
    """Alias for dashboard summary."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_dashboard_summary(campus_id)

@router.get("/dashboard/recent-activity")
async def get_dashboard_recent_activity(
    current_user: dict = admin_auth
):
    """A09: Institutional recent activity audit events."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_campus_activity(campus_id, limit=20)

@router.get("/dashboard/counsellor-workload", response_model=List[CounsellorWorkloadMetric])
async def get_dashboard_counsellor_workload(
    current_user: dict = admin_auth
):
    """A08: Real-time counsellor case loads and capacity overview."""
    campus_id = current_user.get("active_campus_id")
    summary = AdminService.get_dashboard_summary(campus_id)
    return summary.counsellor_workload

# ==========================================
# B. USER AND ROLE MANAGEMENT ENDPOINTS
# ==========================================

@router.get("/users", response_model=UserListResponse)
async def list_campus_users(
    role: Optional[str] = Query(None, description="Filter by role (student, faculty, counsellor, etc.)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search user full name or email"),
    is_active: Optional[bool] = Query(None, description="Filter by membership status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = admin_auth
):
    """A11-A13: List, search, and filter institutional users with role scoping."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.list_users(
        campus_id=campus_id,
        role=role,
        department=department,
        search=search,
        is_active=is_active,
        page=page,
        limit=limit
    )

@router.get("/users/{user_id}", response_model=UserItemResponse)
async def get_user_detail(
    user_id: str = Path(...),
    current_user: dict = admin_auth
):
    """A20: View user details within the institutional campus scope."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_user_details(campus_id, user_id)

@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_staff_member(
    payload: InviteStaffRequest,
    current_user: dict = admin_auth
):
    """A14-A15: Send official institutional invitation to faculty or counsellor."""
    campus_id = current_user.get("active_campus_id")
    admin_id = current_user.get("sub")
    return AdminService.invite_staff(campus_id, admin_id, payload)

@router.get("/invitations", response_model=List[InvitationResponse])
async def list_invitations(
    current_user: dict = admin_auth
):
    """A16: View invitation history and pending dispatch status."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.list_invitations(campus_id)

@router.get("/invitations/{invitation_id}", response_model=InvitationResponse)
async def get_invitation_detail(
    invitation_id: str = Path(...),
    current_user: dict = admin_auth
):
    """View details for a specific invitation."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_invitation(campus_id, invitation_id)

@router.patch("/memberships/{membership_id}", response_model=UserItemResponse)
async def update_campus_membership(
    membership_id: str = Path(..., description="Target User ID"),
    payload: MembershipUpdateRequest = ...,
    current_user: dict = admin_auth
):
    """A17-A19: Manage campus memberships, roles, status, and department assignment."""
    campus_id = current_user.get("active_campus_id")
    admin_id = current_user.get("sub")
    return AdminService.update_membership(campus_id, admin_id, membership_id, payload)

# ==========================================
# C. CAMPUS MANAGEMENT ENDPOINTS
# ==========================================

@router.get("/campus", response_model=CampusDetailResponse)
async def get_campus_info(
    current_user: dict = admin_auth
):
    """A21: View current campus administrative profile and configuration."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_campus_details(campus_id)

@router.patch("/campus", response_model=CampusDetailResponse)
async def update_campus_info(
    payload: CampusUpdateRequest,
    current_user: dict = admin_auth
):
    """A22-A23: Update permitted campus details and SLA configurations."""
    campus_id = current_user.get("active_campus_id")
    admin_id = current_user.get("sub")
    return AdminService.update_campus(campus_id, admin_id, payload)

@router.get("/campus/memberships", response_model=UserListResponse)
async def list_campus_memberships(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = admin_auth
):
    """A24: View all memberships enrolled in this campus."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.list_users(campus_id=campus_id, page=page, limit=limit)

@router.get("/campus/activity")
async def get_campus_activity_stream(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = admin_auth
):
    """A25: Monitor campus activity log."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_campus_activity(campus_id, limit=limit)

# ==========================================
# D. CASE SUPERVISION ENDPOINTS
# ==========================================

@router.get("/cases", response_model=List[AdminCaseListItem])
async def list_supervision_cases(
    priority: Optional[str] = Query(None, description="critical, high, medium, low"),
    state: Optional[str] = Query(None, description="Case state filter"),
    counsellor_id: Optional[str] = Query(None, description="Filter by assigned counsellor"),
    search: Optional[str] = Query(None, description="Search student name, ID or case ID"),
    current_user: dict = admin_auth
):
    """A26-A28: View, filter, and search institutional cases for administrative oversight."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.list_cases(
        campus_id=campus_id,
        priority=priority,
        state=state,
        counsellor_id=counsellor_id,
        overdue_only=False,
        search=search
    )

@router.get("/cases/overdue", response_model=List[AdminCaseListItem])
async def list_overdue_cases(
    current_user: dict = admin_auth
):
    """A30: Dedicated view for monitoring cases that breached SLA deadlines."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.list_cases(campus_id=campus_id, overdue_only=True)

@router.get("/cases/{case_id}", response_model=AdminCaseDetail)
async def get_supervision_case_detail(
    case_id: str = Path(...),
    current_user: dict = admin_auth
):
    """A29: Administrative view of case without exposing confidential clinical counselling notes."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_case_detail(campus_id, case_id)

@router.post("/cases/{case_id}/reassign", response_model=AdminCaseDetail)
async def reassign_case_owner(
    case_id: str = Path(...),
    payload: ReassignCaseRequest = ...,
    current_user: dict = admin_auth
):
    """A31: Supervisor case reassignment with notification and audit event."""
    campus_id = current_user.get("active_campus_id")
    admin_id = current_user.get("sub")
    return AdminService.reassign_case(campus_id, admin_id, case_id, payload)

@router.get("/cases/{case_id}/interventions")
async def get_case_interventions(
    case_id: str = Path(...),
    current_user: dict = admin_auth
):
    """A32: Monitor intervention progress for institutional oversight."""
    campus_id = current_user.get("active_campus_id")
    detail = AdminService.get_case_detail(campus_id, case_id)
    return detail.interventions

@router.get("/cases/{case_id}/timeline")
async def get_case_timeline(
    case_id: str = Path(...),
    current_user: dict = admin_auth
):
    """Monitor state transitions and timeline events."""
    campus_id = current_user.get("active_campus_id")
    detail = AdminService.get_case_detail(campus_id, case_id)
    return detail.timeline_events

# ==========================================
# E. DATA IMPORT MONITORING ENDPOINTS
# ==========================================

@router.get("/imports", response_model=List[ImportJobResponse])
async def list_data_imports(
    current_user: dict = admin_auth
):
    """A34 & A37: View ingestion import history and monitoring status."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.list_imports(campus_id)

@router.get("/imports/{import_id}", response_model=ImportJobResponse)
async def get_import_details(
    import_id: str = Path(...),
    current_user: dict = admin_auth
):
    """A35: View details and statistics of an ingestion job."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_import_details(campus_id, import_id)

@router.get("/imports/{import_id}/errors")
async def get_import_validation_errors(
    import_id: str = Path(...),
    current_user: dict = admin_auth
):
    """A36: View validation errors and failed records for an ingestion batch."""
    campus_id = current_user.get("active_campus_id")
    job = AdminService.get_import_details(campus_id, import_id)
    return {"import_id": import_id, "errors": job.errors or []}

# ==========================================
# F. REPORTS AND ANALYTICS ENDPOINTS
# ==========================================

@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    current_user: dict = admin_auth
):
    """A38-A43: High-level analytics, case statistics, workload distribution, and resolution rates."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.get_analytics_overview(campus_id)

@router.get("/analytics/cases")
async def get_analytics_cases(
    current_user: dict = admin_auth
):
    """A38: Case metrics breakdown."""
    campus_id = current_user.get("active_campus_id")
    overview = AdminService.get_analytics_overview(campus_id)
    return {
        "priority_breakdown": overview.case_volume_by_priority,
        "state_breakdown": overview.case_volume_by_state,
        "resolution_rate_pct": overview.resolution_rate_pct,
        "overdue_rate_pct": overview.overdue_rate_pct
    }

@router.get("/analytics/counsellor-workload")
async def get_analytics_counsellor_workload(
    current_user: dict = admin_auth
):
    """A39: Counsellor workload analytics."""
    campus_id = current_user.get("active_campus_id")
    overview = AdminService.get_analytics_overview(campus_id)
    return overview.counsellor_distribution

@router.get("/analytics/interventions")
async def get_analytics_interventions(
    current_user: dict = admin_auth
):
    """A40: Intervention catalog statistics."""
    campus_id = current_user.get("active_campus_id")
    overview = AdminService.get_analytics_overview(campus_id)
    return {"total_interventions_catalogued": overview.total_interventions_catalogued}

@router.get("/analytics/imports")
async def get_analytics_imports(
    current_user: dict = admin_auth
):
    """A42: Import job summaries."""
    campus_id = current_user.get("active_campus_id")
    overview = AdminService.get_analytics_overview(campus_id)
    return {"total_imports_run": overview.total_imports_run}

# ==========================================
# G. AUDIT MONITORING ENDPOINTS
# ==========================================

@router.get("/audit", response_model=List[AuditLogItemResponse])
async def list_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (case, user, membership, etc.)"),
    action: Optional[str] = Query(None, description="Filter by event action"),
    actor_id: Optional[str] = Query(None, description="Filter by actor user ID"),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = admin_auth
):
    """A45-A48: View and filter cryptographically-chained immutable audit events."""
    campus_id = current_user.get("active_campus_id")
    return AdminService.list_audit_events(
        campus_id=campus_id,
        entity_type=entity_type,
        action=action,
        actor_id=actor_id,
        limit=limit
    )

@router.get("/audit/{event_id}", response_model=AuditLogItemResponse)
async def get_audit_event_detail(
    event_id: str = Path(...),
    current_user: dict = admin_auth
):
    """A47: View individual audit event with cryptographic verification hashes."""
    campus_id = current_user.get("active_campus_id")
    events = AdminService.list_audit_events(campus_id=campus_id, limit=500)
    for ev in events:
        if ev.id == event_id:
            return ev
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Audit event not found")

# ==========================================
# H. ADMIN PROFILE ENDPOINTS
# ==========================================

@router.get("/profile", response_model=AdminProfileResponse)
async def get_my_admin_profile(
    current_user: dict = admin_auth
):
    """A49: View administrator profile details."""
    campus_id = current_user.get("active_campus_id")
    user_id = current_user.get("sub")
    return AdminService.get_profile(campus_id, user_id)

@router.patch("/profile", response_model=AdminProfileResponse)
async def update_my_admin_profile(
    payload: AdminProfileUpdateRequest,
    current_user: dict = admin_auth
):
    """A50: Update permitted profile fields."""
    campus_id = current_user.get("active_campus_id")
    user_id = current_user.get("sub")
    return AdminService.update_profile(campus_id, user_id, payload)

@router.post("/profile/change-password")
async def change_admin_password(
    payload: AdminChangePasswordRequest,
    current_user: dict = admin_auth
):
    """A51: Secure password management through institutional security provider."""
    campus_id = current_user.get("active_campus_id")
    user_id = current_user.get("sub")
    return AdminService.change_password(campus_id, user_id, payload)

