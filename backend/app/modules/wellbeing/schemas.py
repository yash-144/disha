from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WellbeingBase(BaseModel):
    pass

class WellbeingResponse(WellbeingBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
