from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MlBase(BaseModel):
    pass

class MlResponse(MlBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
