from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CasesBase(BaseModel):
    pass

class CasesResponse(CasesBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
