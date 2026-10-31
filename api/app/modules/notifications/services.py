import base64
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DishaBaseException, EntityNotFoundError
from app.modules.audit.services import AuditService
from app.modules.campus.models import Campus
from app.modules.notifications.models import Notification, NotificationOutbox
from app.shared.utils import utc_now


async def campus_channels(db: AsyncSession, campus_id: str) -> List[str]:
    row = (await db.execute(select(Campus.settings).where(Campus.id == campus_id))).scalar_one_or_none()
    channels = (row or {}).get("notification_channels") or ["in_app"]
    return sorted(set(channels) | {"in_app"})


class NotificationOutboxService:
    """Writes delivery intents. Call inside the transaction of the change that caused them (CASE-SM-06)."""

    @staticmethod
    async def enqueue(
        db: AsyncSession,
        *,
        campus_id: str,
        recipient_id: str,
        template_key: str,
        idempotency_key: str,
        safe_payload: Optional[dict] = None,
        case_id: Optional[str] = None,
        channels: Optional[Sequence[str]] = None,
    ) -> List[NotificationOutbox]:
        if channels is None:
            channels = await campus_channels(db, campus_id)
        created: List[NotificationOutbox] = []
        for channel in channels:
            key = idempotency_key if channel == "in_app" else f"{idempotency_key}:{channel}"
            exists = await db.execute(select(NotificationOutbox.id).where(NotificationOutbox.idempotency_key == key))
            if exists.scalar_one_or_none():
                continue
            row = NotificationOutbox(
                campus_id=campus_id,
                case_id=case_id,
                recipient_id=recipient_id,
                adapter_key=channel,
                template_key=template_key,
                safe_payload=safe_payload or {},
                status="pending",
                attempts=0,
                next_attempt_at=utc_now(),
                idempotency_key=key,
            )
            db.add(row)
            created.append(row)
        if created:
            await db.flush()
        return created


def _encode_cursor(created_at: datetime, nid: str) -> str:
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{nid}".encode()).decode()


def _decode_cursor(cursor: str) -> Tuple[datetime, str]:
    try:
        ts, nid = base64.urlsafe_b64decode(cursor.encode()).decode().split("|", 1)
        return datetime.fromisoformat(ts), nid
    except Exception:
        raise DishaBaseException("Invalid cursor", 400)


class InboxService:
    @staticmethod
    async def list_for_user(
        db: AsyncSession, campus_id: str, user_id: str, unread_only: bool, limit: int, cursor: Optional[str]
    ):
        stmt = select(Notification).where(Notification.recipient_id == user_id, Notification.campus_id == campus_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712
        if cursor:
            c_ts, c_id = _decode_cursor(cursor)
            stmt = stmt.where(
                (Notification.created_at < c_ts) | ((Notification.created_at == c_ts) & (Notification.id < c_id))
            )
        stmt = stmt.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit + 1)
        rows = list((await db.execute(stmt)).scalars().all())
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id)
        return rows, next_cursor

    @staticmethod
    async def unread_count(db: AsyncSession, campus_id: str, user_id: str) -> int:
        return (
            await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.recipient_id == user_id,
                    Notification.campus_id == campus_id,
                    Notification.is_read == False,  # noqa: E712
                )
            )
        ).scalar_one()

    @staticmethod
    async def mark_read(db: AsyncSession, campus_id: str, user_id: str, notification_id: str) -> Notification:
        # another user's (or campus's) notification is indistinguishable from a missing one
        res = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_id == user_id,
                Notification.campus_id == campus_id,
            )
        )
        notif = res.scalar_one_or_none()
        if not notif:
            raise EntityNotFoundError("Notification", notification_id)
        if not notif.is_read:
            notif.is_read = True
            await AuditService.record_event(
                db, actor_id=user_id, campus_id=campus_id, entity_type="notification",
                entity_id=notif.id, action="NOTIFICATION_READ", event_metadata={},
            )
        await db.flush()
        return notif

    @staticmethod
    async def mark_all_read(db: AsyncSession, campus_id: str, user_id: str) -> int:
        res = await db.execute(
            update(Notification)
            .where(
                Notification.recipient_id == user_id,
                Notification.campus_id == campus_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        count = res.rowcount or 0
        if count:
            await AuditService.record_event(
                db, actor_id=user_id, campus_id=campus_id, entity_type="notification",
                entity_id=user_id, action="NOTIFICATIONS_READ_ALL", event_metadata={"count": count},
            )
        return count


class OutboxAdminService:
    @staticmethod
    async def list_outbox(db: AsyncSession, campus_id: str, status: Optional[str], limit: int, offset: int):
        stmt = select(NotificationOutbox).where(NotificationOutbox.campus_id == campus_id)
        if status:
            stmt = stmt.where(NotificationOutbox.status == status)
        stmt = stmt.order_by(NotificationOutbox.created_at.desc()).limit(limit).offset(offset)
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def retry(db: AsyncSession, campus_id: str, actor_id: str, outbox_id: str) -> NotificationOutbox:
        res = await db.execute(
            select(NotificationOutbox).where(NotificationOutbox.id == outbox_id, NotificationOutbox.campus_id == campus_id)
        )
        row = res.scalar_one_or_none()
        if not row:
            raise EntityNotFoundError("OutboxItem", outbox_id)
        if row.status not in ("dead_letter", "failed"):
            raise DishaBaseException("Only dead-lettered or failed items can be retried", 409)
        row.status = "pending"
        row.attempts = 0
        row.last_error_code = None
        row.next_attempt_at = utc_now()
        await AuditService.record_event(
            db, actor_id=actor_id, campus_id=campus_id, entity_type="notification_outbox",
            entity_id=row.id, action="OUTBOX_RETRY_REQUESTED", event_metadata={"adapter_key": row.adapter_key},
        )
        await db.flush()
        return row
