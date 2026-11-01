from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AttendanceRecordCreate(BaseModel):
    section_id: str
    student_id: str
    date: str  # YYYY-MM-DD
    status: str  # Present, Late, Absent


class AssessmentCreate(BaseModel):
    section_id: str
    title: str
    assessment_type: str = "quiz"
    total_marks: float = 100.0
    clo_code: Optional[str] = "CLO-1"
    due_at: Optional[datetime] = None


class MarkEntry(BaseModel):
    assessment_id: str
    student_id: str
    score: float
    feedback: Optional[str] = None


class SignalReviewRequest(BaseModel):
    decision: str  # approve, modify, dismiss
    reason: Optional[str] = None
    selected_intervention_key: Optional[str] = "mentor_check_in"


class CaseTaskCreate(BaseModel):
    domain: str = "academic"
    generic_label: str
    due_days: Optional[int] = 3


class FollowUpCreate(BaseModel):
    follow_up_type: str = "contact_attempt"
    contact_status: str = "student_reached"
    proof_kind: str = "staff_attestation"
    sanitized_note: str


class CaseOutcomeCreate(BaseModel):
    outcome_status: str  # helped, not_helped, mixed, unknown
    rationale: str
    evidence_kind: str = "academic_record"


class FacultyProfileResponse(BaseModel):
    id: str
    user_id: str
    campus_id: str
    title: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
