from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RosterBase(BaseModel):
    pass

class RosterResponse(RosterBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
