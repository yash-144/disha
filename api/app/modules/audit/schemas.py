from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditBase(BaseModel):
    pass

class AuditResponse(AuditBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
