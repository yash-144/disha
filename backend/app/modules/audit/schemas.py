from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AuditBase(BaseModel):
    pass


class AuditResponse(AuditBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditVerificationResponse(BaseModel):
    campus_id: str
    is_valid: bool
    total_events: int
    error: Optional[str] = None
    broken_index: Optional[int] = None


class AuditEventDetailResponse(BaseModel):
    id: str
    actor_id: str
    campus_id: str
    entity_type: str
    entity_id: str
    action: str
    event_metadata: Optional[Dict[str, Any]] = None
    prev_hash: Optional[str] = None
    event_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
