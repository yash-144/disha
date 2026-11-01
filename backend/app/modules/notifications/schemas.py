from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationsBase(BaseModel):
    pass

class NotificationsResponse(NotificationsBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
