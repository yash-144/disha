from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ==========================================
# A. DASHBOARD SCHEMAS
# ==========================================

class CounsellorWorkloadMetric(BaseModel):
    user_id: str
    full_name: str
    email: str
    department: Optional[str] = None
    active_cases: int
    overdue_cases: int
    resolved_cases: int
    availability_status: str

class AdminDashboardSummary(BaseModel):
    total_students: int
    total_faculty: int
    total_counsellors: int
    total_active_cases: int
    pending_cases: int
    overdue_cases: int
    resolved_cases: int
    counsellor_workload: List[CounsellorWorkloadMetric]
    recent_activities: List[Dict[str, Any]]
    administrative_notifications: List[Dict[str, Any]]

# ==========================================
# B. USER AND ROLE SCHEMAS
# ==========================================

class UserItemResponse(BaseModel):
    id: str
    email: str
    full_name: str
    roles: List[str]
    campus_id: str
    department: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserListResponse(BaseModel):
    items: List[UserItemResponse]
    total: int
    page: int
    limit: int

class InviteStaffRequest(BaseModel):
    email: str = Field(..., min_length=5, description="Institutional email address")
    full_name: str = Field(..., min_length=2)
    role: str = Field(..., description="counsellor, faculty, mentor, hod, finance, placement")
    department: Optional[str] = None

class InvitationResponse(BaseModel):
    id: str
    campus_id: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    status: str
    invited_by: str
    created_at: datetime
    expires_at: datetime

class MembershipUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    department: Optional[str] = None

# ==========================================
# C. CAMPUS MANAGEMENT SCHEMAS
# ==========================================

class CampusDetailResponse(BaseModel):
    id: str
    name: str
    code: str
    created_at: datetime
    configuration: Optional[Dict[str, Any]] = None
    active_members_count: int

class CampusUpdateRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None

# ==========================================
# D. CASE SUPERVISION SCHEMAS
# ==========================================

class AdminCaseListItem(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    student_ref: Optional[str] = None
    department: Optional[str] = None
    priority: str
    state: str
    primary_owner_user_id: Optional[str] = None
    counsellor_name: Optional[str] = None
    due_at: Optional[datetime] = None
    is_overdue: bool
    is_escalated: bool
    selected_intervention_key: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

class AdminCaseDetail(BaseModel):
    id: str
    campus_id: str
    student_id: str
    student_name: Optional[str] = None
    student_ref: Optional[str] = None
    department: Optional[str] = None
    priority: str
    state: str
    primary_owner_user_id: Optional[str] = None
    counsellor_name: Optional[str] = None
    due_at: Optional[datetime] = None
    is_overdue: bool
    is_escalated: bool
    selected_intervention_key: Optional[str] = None
    intervention_label: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime
    interventions: List[Dict[str, Any]]
    follow_ups: List[Dict[str, Any]]
    timeline_events: List[Dict[str, Any]]

class ReassignCaseRequest(BaseModel):
    new_counsellor_user_id: str = Field(..., description="Target counsellor user ID")
    reassignment_reason: str = Field(..., min_length=3, description="Operational reason for supervisor reassignment")
    expected_version: int = Field(..., description="Current case version for optimistic concurrency locking")

# ==========================================
# E. DATA IMPORT MONITORING SCHEMAS
# ==========================================

class ImportValidationError(BaseModel):
    row: int
    column: str
    error: str
    raw_value: Optional[str] = None

class ImportJobResponse(BaseModel):
    id: str
    campus_id: str
    file_name: str
    source_type: str
    status: str
    total_records: int
    processed_records: int
    error_count: int
    errors: Optional[List[ImportValidationError]] = None
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None

# ==========================================
# F. REPORTS AND ANALYTICS SCHEMAS
# ==========================================

class AnalyticsOverviewResponse(BaseModel):
    campus_id: str
    case_volume_by_priority: Dict[str, int]
    case_volume_by_state: Dict[str, int]
    counsellor_distribution: List[Dict[str, Any]]
    resolution_rate_pct: float
    overdue_rate_pct: float
    total_interventions_catalogued: int
    total_imports_run: int

# ==========================================
# G. AUDIT MONITORING SCHEMAS
# ==========================================

class AuditLogItemResponse(BaseModel):
    id: str
    actor_id: str
    campus_id: str
    entity_type: str
    entity_id: str
    action: str
    metadata: Dict[str, Any]
    prev_hash: Optional[str] = None
    curr_hash: Optional[str] = None
    created_at: datetime

# ==========================================
# H. ADMIN PROFILE SCHEMAS
# ==========================================

class AdminProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    roles: List[str]
    campus_id: str
    department: Optional[str] = None
    created_at: datetime

class AdminProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    department: Optional[str] = None

class AdminChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
