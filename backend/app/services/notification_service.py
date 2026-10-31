import uuid
from typing import Dict, List, Optional, Tuple
from app.core.database import db
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from app.shared.utils import utc_now

class NotificationService:
    @staticmethod
    def list_notifications(
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        with db._lock:
            notifs = [
                n for n in db.notifications.values()
                if n.get("user_id") == user_id
            ]
            if unread_only:
                notifs = [n for n in notifs if not n.get("is_read")]

            notifs.sort(key=lambda x: x.get("created_at", utc_now()), reverse=True)
            total = len(notifs)
            start = (page - 1) * page_size
            end = start + page_size
            return notifs[start:end], total

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> dict:
        with db._lock:
            n = db.notifications.get(notification_id)
            if not n:
                raise EntityNotFoundError("Notification", notification_id)
            if n.get("user_id") != user_id:
                raise PermissionDeniedError("Unauthorized: You cannot access notifications for another user")

            n["is_read"] = True
            n["updated_at"] = utc_now()
            return n

    @staticmethod
    def emit_notification(
        user_id: str,
        title: str,
        message: str,
        category: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> dict:
        with db._lock:
            notif_id = str(uuid.uuid4())
            notif = {
                "id": notif_id,
                "user_id": user_id,
                "title": title,
                "message": message,
                "category": category,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "is_read": False,
                "created_at": utc_now()
            }
            db.notifications[notif_id] = notif
            return notif

