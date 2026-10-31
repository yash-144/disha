from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UpcomingFollowUpItem(BaseModel):
    id: str
    case_id: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    title: str
    scheduled_at: datetime
    follow_up_type: str
    status: str

class OverdueCaseItem(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    priority: str
    state: str
    due_at: Optional[datetime] = None
    selected_intervention_key: Optional[str] = None
    is_escalated: bool = False

class CounsellorDashboardSummary(BaseModel):
    assigned_students_count: int
    assigned_cases_count: int
    pending_cases_count: int
    active_cases_count: int
    overdue_cases_count: int

class CounsellorDashboardResponse(BaseModel):
    summary: CounsellorDashboardSummary
    upcoming_followups: List[UpcomingFollowUpItem]
    overdue_cases: List[OverdueCaseItem]

class CounsellorProfileResponse(BaseModel):
    id: str
    user_id: str
    campus_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    specializations: List[str] = []
    qualification: Optional[str] = None
    availability_status: str
    assigned_cohorts: List[str] = []
    onboarding_status: str
    created_at: datetime
    updated_at: datetime

class CounsellorProfileUpdateRequest(BaseModel):
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    specializations: Optional[List[str]] = None
    qualification: Optional[str] = None
    availability_status: Optional[str] = None

class StudentListItem(BaseModel):
    id: str
    external_ref: str
    display_name: str
    department: str
    course: str
    cohort_code: str
    academic_year: str
    enrollment_status: str
    active_case_count: int = 0

class StudentDetailResponse(BaseModel):
    id: str
    institution_id: str
    external_ref: str
    display_name: str
    department: str
    course: str
    cohort_code: str
    academic_year: str
    enrollment_status: str
    created_at: datetime
    assigned_cases: List[Dict[str, Any]] = []

class StudentObservationItem(BaseModel):
    id: str
    institution_id: str
    student_id: str
    domain: str
    title: str
    value: str
    event_at: datetime
    quality_state: str
    provenance: str

class StudentSupportHistoryItem(BaseModel):
    case_id: str
    priority: str
    state: str
    intervention: Optional[str] = None
    created_at: datetime
    closed_at: Optional[datetime] = None
    outcome: Optional[Dict[str, Any]] = None
    follow_up_count: int = 0

