from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IngestionBase(BaseModel):
    pass

class IngestionResponse(IngestionBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
