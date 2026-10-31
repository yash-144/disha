from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PolicyBase(BaseModel):
    pass

class PolicyResponse(PolicyBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
