from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StudentIdentityBase(BaseModel):
    pass

class StudentIdentityResponse(StudentIdentityBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
