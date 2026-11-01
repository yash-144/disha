from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationItem(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    category: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    is_read: bool
    created_at: datetime

class NotificationMarkReadResponse(BaseModel):
    id: str
    is_read: bool
    updated_at: datetime

