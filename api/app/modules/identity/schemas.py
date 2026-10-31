from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IdentityBase(BaseModel):
    pass

class IdentityResponse(IdentityBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
