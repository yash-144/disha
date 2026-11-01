from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.shared.enums import CaseState, CaseStatus

class CaseTransitionRequest(BaseModel):
    target_state: str = Field(..., description="Canonical CaseState target or compatible legacy CaseStatus")
    expected_version: int = Field(..., description="Optimistic locking version counter")
    reason_code: Optional[str] = Field(None, description="Standardized operational reason code")
    notes: Optional[str] = Field(None, description="Explanatory notes or rationale for transition")
    new_owner_id: Optional[str] = Field(None, description="Assigned counsellor ID (required when assigning/reassigning)")
    due_at: Optional[datetime] = Field(None, description="SLA target completion timestamp")
    has_follow_up: Optional[bool] = Field(False, description="Whether prerequisite follow-up is verified")
    has_outcome: Optional[bool] = Field(False, description="Whether prerequisite outcome is verified")

class CaseCreateRequest(BaseModel):
    student_id: str = Field(..., description="UUID of student from disha_roster")
    title: str = Field(..., description="Case summary or title")
    description: Optional[str] = Field(None, description="Detailed case description")
    priority: Optional[str] = Field("medium", description="Priority level: low, medium, high, urgent")
    initial_state: Optional[str] = Field(CaseState.ACTION_PLANNED.value, description="Initial canonical case state")
    assigned_counsellor_id: Optional[str] = Field(None, description="Initial assigned counsellor ID")
    due_date: Optional[datetime] = Field(None, description="Target SLA completion deadline")

class CaseUpdateRequest(BaseModel):
    expected_version: int = Field(..., description="Optimistic locking version counter")
    title: Optional[str] = Field(None, description="Updated case title")
    description: Optional[str] = Field(None, description="Updated description")
    priority: Optional[str] = Field(None, description="Updated priority")
    due_date: Optional[datetime] = Field(None, description="Updated target SLA deadline")

class CaseAssignRequest(BaseModel):
    expected_version: int = Field(..., description="Optimistic locking version counter")
    counsellor_id: str = Field(..., description="ID of assigned counsellor")
    due_date: Optional[datetime] = Field(None, description="Target SLA deadline")
    notes: Optional[str] = Field(None, description="Assignment rationale or guidance")

class CaseReopenRequest(BaseModel):
    expected_version: int = Field(..., description="Optimistic locking version counter")
    reason_code: Optional[str] = Field(None, description="Standardized reopening reason code")
    notes: Optional[str] = Field(None, description="Detailed rationale for reopening")

class CaseDismissRequest(BaseModel):
    expected_version: int = Field(..., description="Optimistic locking version counter")
    reason_code: Optional[str] = Field(None, description="Standardized dismissal reason code")
    notes: Optional[str] = Field(None, description="Mandatory rationale for dismissing case")

class CaseDetailResponse(BaseModel):
    id: str
    campus_id: str
    student_id: str
    student_name: Optional[str] = None
    student_ref: Optional[str] = None
    department: Optional[str] = None
    state: CaseState
    legacy_status: CaseStatus
    priority: str
    primary_owner_user_id: Optional[str] = None
    owner_name: Optional[str] = None
    due_at: Optional[datetime] = None
    is_overdue: bool = False
    is_escalated: bool = False
    selected_intervention_key: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None

class CaseEventResponse(BaseModel):
    id: str
    case_id: str
    actor_id: str
    event_type: str
    from_state: str
    to_state: str
    reason_code: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
