from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class NotificationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    notification_type: str
    title: str
    body: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    is_read: bool
    created_at: datetime


class NotificationPage(BaseModel):
    items: List[NotificationItem]
    next_cursor: Optional[str] = None


class UnreadCount(BaseModel):
    unread: int


class OutboxItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: Optional[str] = None
    adapter_key: str
    template_key: str
    status: str
    attempts: int
    next_attempt_at: datetime
    last_error_code: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
