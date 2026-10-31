from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Domain = Literal["academic", "attendance", "finance", "counselling", "other"]


class CaseCreate(BaseModel):
    flag_id: str = Field(max_length=64)
    student_id: str = Field(max_length=64)
    intervention_id: Optional[str] = Field(default=None, max_length=64)
    reason_codes: List[str] = Field(default_factory=list)
    tier: Optional[str] = None


class Transition(BaseModel):
    to_state: str
    version: int  # clients must send the version they read (CASE-SM-05)
    reason_code: Optional[str] = Field(default=None, max_length=64)


class Assign(BaseModel):
    owner_id: str = Field(max_length=64)
    due_at: datetime
    version: int
    reason_code: Optional[str] = Field(default=None, max_length=64)


class TaskCreate(BaseModel):
    domain: Domain
    generic_label: str = Field(max_length=200)
    assignee_id: Optional[str] = None
    due_at: Optional[datetime] = None
    restricted_details: Optional[Dict[str, Any]] = None  # stored apart; only for finance/counselling


class TaskState(BaseModel):
    to_state: Literal["accepted", "in_progress", "completed", "cancelled"]


class CaseOutcomeIn(BaseModel):
    outcome: Literal["improved", "no_change", "worse"]
    intervention_id: str
    reason_codes: List[str] = Field(default_factory=list)
    tier: Optional[str] = None
    checkpoint: Optional[str] = None


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    flag_id: str
    student_ref: str
    intervention_id: Optional[str]
    tier: Optional[str]
    reason_codes: list
    state: str
    owner_id: Optional[str]
    due_at: Optional[datetime]
    is_escalated: bool
    version: int
    cycle: int
    created_at: datetime


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_type: str
    actor_id: Optional[str]
    actor_kind: str
    from_state: Optional[str]
    to_state: Optional[str]
    reason_code: Optional[str]
    created_at: datetime


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_id: str
    domain: str
    generic_label: str
    state: str
    assignee_id: Optional[str]
    due_at: Optional[datetime]
    is_escalated: bool
