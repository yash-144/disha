from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

FOLLOW_UP_TYPES = ("contact_attempt", "student_response", "support_delivered", "follow_up_check")
PROOF_KINDS = (
    "staff_attestation", "student_confirmation", "appointment_record", "service_provider_confirmation", "none",
)
CONTACT_STATUSES = ("attempted", "student_reached", "unreachable", "declined")
OUTCOME_STATUSES = ("helped", "not_helped", "mixed", "unknown")
PROGRESS_STATES = ("not_started", "in_progress", "completed", "cancelled")

FollowUpType = Literal["contact_attempt", "student_response", "support_delivered", "follow_up_check"]
ProofKind = Literal[
    "staff_attestation", "student_confirmation", "appointment_record", "service_provider_confirmation", "none"
]
ContactStatus = Literal["attempted", "student_reached", "unreachable", "declined"]
OutcomeStatus = Literal["helped", "not_helped", "mixed", "unknown"]


class CatalogueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campus_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool


class CatalogueCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)


class CatalogueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class InterventionCreate(BaseModel):
    catalogue_id: str
    description: Optional[str] = Field(None, max_length=4000)
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None


class InterventionProgressUpdate(BaseModel):
    progress: Literal["in_progress", "completed", "cancelled"]
    description: Optional[str] = Field(None, max_length=4000)
    target_date: Optional[datetime] = None


class OutcomeCreate(BaseModel):
    intervention_id: str
    completion_status: OutcomeStatus
    outcome_notes: Optional[str] = Field(None, max_length=4000)
    completed_at: Optional[datetime] = None


class OutcomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_id: str
    intervention_id: str
    completion_status: str
    outcome_notes: Optional[str] = None
    completed_at: datetime
    created_at: datetime


class InterventionOut(BaseModel):
    id: str
    case_id: str
    catalogue_id: str
    name: str
    category: Optional[str] = None
    counsellor_id: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    progress: str
    outcome: Optional[OutcomeOut] = None
    created_at: datetime
    updated_at: datetime


class FollowUpCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=500)
    description: Optional[str] = Field(None, max_length=4000)
    scheduled_at: datetime
    follow_up_type: FollowUpType = "follow_up_check"
    proof_kind: Optional[ProofKind] = None


class FollowUpReschedule(BaseModel):
    scheduled_at: datetime
    title: Optional[str] = Field(None, min_length=2, max_length=500)


class FollowUpComplete(BaseModel):
    contact_status: Optional[ContactStatus] = None
    proof_kind: Optional[ProofKind] = None
    completion_notes: Optional[str] = Field(None, max_length=4000)


class FollowUpCancel(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500)


class FollowUpNoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class FollowUpNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    author_id: str
    content: str
    created_at: datetime


class FollowUpOut(BaseModel):
    id: str
    case_id: str
    counsellor_id: str
    title: str
    description: Optional[str] = None
    follow_up_type: str
    contact_status: Optional[str] = None
    proof_kind: Optional[str] = None
    scheduled_at: datetime
    status: str
    is_overdue: bool = False
    is_escalated: bool = False
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    notes: List[FollowUpNoteOut] = []
    created_at: datetime
