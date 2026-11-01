from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RewardsBase(BaseModel):
    pass

class RewardsResponse(RewardsBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
