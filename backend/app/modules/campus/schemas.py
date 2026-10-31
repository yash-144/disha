from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CampusBase(BaseModel):
    pass

class CampusResponse(CampusBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
