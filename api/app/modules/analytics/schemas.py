from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnalyticsBase(BaseModel):
    pass

class AnalyticsResponse(AnalyticsBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
