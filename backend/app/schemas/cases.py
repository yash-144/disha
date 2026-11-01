from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CaseListItem(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    student_ref: Optional[str] = None
    department: Optional[str] = None
    priority: str
    state: str
    due_at: Optional[datetime] = None
    selected_intervention_key: Optional[str] = None
    is_escalated: bool = False
    version: int
    created_at: datetime
    updated_at: datetime

class CaseNoteResponse(BaseModel):
    id: str
    case_id: str
    author_user_id: str
    author_name: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class CaseNoteCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Content of the case note")

class CaseStatusUpdateRequest(BaseModel):
    target_state: str = Field(..., description="Target case state to transition to")
    reason_code: Optional[str] = None
    notes: Optional[str] = None
    expected_version: int = Field(..., description="Optimistic locking version counter")

class CaseAcceptRequest(BaseModel):
    expected_version: int = Field(..., description="Current case version for optimistic locking")
    acceptance_notes: Optional[str] = None

class CaseCloseRequest(BaseModel):
    expected_version: int = Field(..., description="Current case version for optimistic locking")
    reason_code: str = Field(default="INTERVENTION_COMPLETED", description="Standardized closure reason code")
    closing_notes: str = Field(..., min_length=5, description="Summary notes explaining case resolution")

class CaseTimelineEventResponse(BaseModel):
    id: str
    case_id: str
    actor_user_id: str
    actor_name: Optional[str] = None
    event_type: str
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    reason_code: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime

class CaseDetailResponse(BaseModel):
    id: str
    institution_id: str
    student: Dict[str, Any]
    originating_signal_id: Optional[str] = None
    selected_intervention: Optional[Dict[str, Any]] = None
    priority: str
    state: str
    primary_owner_user_id: str
    primary_owner_name: Optional[str] = None
    due_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None
    is_escalated: bool = False
    version: int
    created_at: datetime
    updated_at: datetime
    observations: List[Dict[str, Any]] = []
    follow_ups: List[Dict[str, Any]] = []
    notes: List[CaseNoteResponse] = []
    timeline: List[CaseTimelineEventResponse] = []
    outcome: Optional[Dict[str, Any]] = None

