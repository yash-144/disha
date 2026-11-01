from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ASSIGNABLE_ROLES = {
    "faculty", "mentor", "hod", "counsellor", "finance", "placement", "leadership", "institution_admin",
}
CHANNELS = {"in_app", "email", "sms"}


class EscalationLevel(BaseModel):
    after_hours: int = Field(0, ge=0, le=24 * 30, description="Hours past the deadline before this level fires")
    target: str = Field("role:hod", pattern=r"^(role:[a-z_]+|contact)$")


class CampusSettings(BaseModel):
    """Per-campus configuration. Escalation and channel choices are read by the worker."""
    timezone: str = "Asia/Kolkata"
    notification_channels: List[str] = ["in_app"]
    escalation_levels: List[EscalationLevel] = [EscalationLevel()]
    escalation_contact_user_id: Optional[str] = None
    followup_grace_hours: int = Field(0, ge=0, le=24 * 30)

    @field_validator("notification_channels")
    @classmethod
    def _channels(cls, v):
        bad = set(v) - CHANNELS
        if bad:
            raise ValueError(f"unknown channels: {sorted(bad)}")
        return sorted(set(v) | {"in_app"})  # in-app delivery is always on

    @field_validator("escalation_levels")
    @classmethod
    def _levels(cls, v):
        if not v:
            raise ValueError("at least one escalation level is required")
        hours = [lvl.after_hours for lvl in v]
        if hours != sorted(hours):
            raise ValueError("escalation levels must be ordered by after_hours")
        return v


class CampusSettingsUpdate(BaseModel):
    """Partial update; omitted keys keep their current value."""
    model_config = ConfigDict(extra="forbid")
    timezone: Optional[str] = None
    notification_channels: Optional[List[str]] = None
    escalation_levels: Optional[List[EscalationLevel]] = None
    escalation_contact_user_id: Optional[str] = None
    followup_grace_hours: Optional[int] = Field(None, ge=0, le=24 * 30)


class CampusCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    code: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    settings: Optional[CampusSettings] = None


class CampusUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=300)
    settings: Optional[CampusSettingsUpdate] = None


class CampusResponse(BaseModel):
    id: str
    name: str
    code: str
    is_active: bool
    settings: CampusSettings
    created_at: datetime
    updated_at: datetime


class InviteCreateRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: str
    department: Optional[str] = Field(None, max_length=200)
    expires_in_days: int = Field(7, ge=1, le=30)


class InviteResponse(BaseModel):
    id: str
    campus_id: str
    email: str
    role: str
    department: Optional[str] = None
    status: str  # pending | accepted | revoked | expired
    expires_at: datetime
    created_by: str
    created_at: datetime
    accepted_at: Optional[datetime] = None


class MembershipUpdateRequest(BaseModel):
    role: Optional[str] = None
    department: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class MembershipItem(BaseModel):
    membership_id: str
    user_id: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool
    user_is_active: bool
    created_at: datetime


class CounsellorWorkload(BaseModel):
    user_id: str
    full_name: str
    active_cases: int
    overdue_cases: int
    availability_status: Optional[str] = None


class CampusDashboard(BaseModel):
    total_students: int
    staff_by_role: dict
    active_cases: int
    overdue_cases: int
    escalated_cases: int
    pending_invites: int
    dead_letter_notifications: int
    counsellor_workload: List[CounsellorWorkload]
