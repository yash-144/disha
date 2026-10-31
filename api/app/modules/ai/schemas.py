from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AiBase(BaseModel):
    pass

class AiResponse(AiBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
