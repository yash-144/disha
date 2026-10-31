from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.interventions.schemas import FollowUpOut

SessionMode = Literal["in_person", "video", "phone"]
Availability = Literal["available", "in_session", "away"]


class ProfileUpsert(BaseModel):
    department: Optional[str] = Field(None, max_length=200)
    specialisation: Optional[str] = Field(None, max_length=300)
    designation: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=40)
    availability_status: Optional[Availability] = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    campus_id: str
    department: Optional[str] = None
    specialisation: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    availability_status: str
    is_active: bool


class SessionCreate(BaseModel):
    student_id: str
    case_id: Optional[str] = None
    counsellor_id: Optional[str] = Field(None, description="Only HOD / platform admin may schedule for someone else")
    scheduled_at: datetime
    duration_minutes: int = Field(45, ge=15, le=240)
    mode: SessionMode = "in_person"
    location: Optional[str] = Field(None, max_length=300)


class SessionReschedule(BaseModel):
    scheduled_at: datetime
    duration_minutes: Optional[int] = Field(None, ge=15, le=240)
    location: Optional[str] = Field(None, max_length=300)


class SessionCancel(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500)


class SessionOut(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    case_id: Optional[str] = None
    counsellor_id: str
    scheduled_at: datetime
    duration_minutes: int
    mode: str
    location: Optional[str] = None
    status: str
    cancel_reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class NoteCreate(BaseModel):
    student_id: str
    case_id: Optional[str] = None
    session_id: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=8000)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    case_id: Optional[str] = None
    session_id: Optional[str] = None
    author_id: str
    content: str
    created_at: datetime


class AssignmentCreate(BaseModel):
    counsellor_id: str
    student_id: str


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    counsellor_id: str
    student_id: str
    is_active: bool
    assigned_at: datetime


class CaseloadItem(BaseModel):
    case_id: str
    student_id: str
    student_name: Optional[str] = None
    student_ref: Optional[str] = None
    department: Optional[str] = None
    state: str
    priority: str
    due_at: Optional[datetime] = None
    is_overdue: bool
    is_escalated: bool
    version: int
    updated_at: datetime


class StudentItem(BaseModel):
    student_id: str
    student_ref: str
    full_name: str
    department: Optional[str] = None
    cohort_code: Optional[str] = None
    open_cases: int


class CounsellorDashboard(BaseModel):
    active_cases: int
    overdue_cases: int
    escalated_cases: int
    upcoming_sessions: int
    overdue_followups: int
    unread_notifications: int
    upcoming_followups: List[FollowUpOut]
    next_sessions: List[SessionOut]
