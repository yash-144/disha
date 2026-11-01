from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CounsellingBase(BaseModel):
    pass

class CounsellingResponse(CounsellingBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
