from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class FollowUpScheduleRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Title of the follow-up")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    follow_up_type: str = Field(default="counselling_session", description="in_person_session, check_in_call, academic_review")
    notes: Optional[str] = None
    proof_kind: Optional[str] = None

class FollowUpCompleteRequest(BaseModel):
    completion_notes: Optional[str] = Field(None, description="Notes recorded upon completing follow-up")
    proof_data: Optional[str] = None

class FollowUpNoteRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Follow-up note content")

class FollowUpResponse(BaseModel):
    id: str
    institution_id: str
    case_id: str
    title: str
    follow_up_type: str
    contact_status: str
    scheduled_at: datetime
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    notes: Optional[str] = None
    proof_kind: Optional[str] = None
    status: str
    created_at: datetime

