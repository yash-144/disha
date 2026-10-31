import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user
from app.services.notification_service import NotificationService
from app.schemas.notifications import NotificationItem, NotificationMarkReadResponse
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=PaginatedResponse[NotificationItem])
async def list_my_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """C10: Retrieve notifications, assignments, follow-up reminders, and overdue alerts."""
    user_id = current_user.get("sub")
    items, total = NotificationService.list_notifications(
        user_id=user_id,
        unread_only=unread_only,
        page=page,
        page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.patch("/{notification_id}/read", response_model=NotificationMarkReadResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read with ownership verification."""
    user_id = current_user.get("sub")
    notif = NotificationService.mark_as_read(notification_id, user_id)
    return NotificationMarkReadResponse(
        id=notif["id"],
        is_read=notif["is_read"],
        updated_at=notif.get("updated_at", notif.get("created_at"))
    )
