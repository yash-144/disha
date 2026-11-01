"""Delivery adapters for the notification outbox (blueprint 07 OUT-01..OUT-03).

``in_app`` is always available. ``email`` needs SMTP settings in the environment; ``sms`` has no
provider wired yet. An adapter that is not configured never reports success: the dispatcher
leaves the row ``pending`` and logs a warning.
"""
import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import User
from app.modules.notifications import templates
from app.modules.notifications.models import Notification, NotificationOutbox
from app.shared.utils import utc_now

logger = logging.getLogger("disha.notifications.providers")


class ProviderNotConfigured(Exception):
    """The adapter exists but has no credentials/endpoint; nothing was sent."""


class DeliveryError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class DeliveryProvider:
    key = ""

    def is_configured(self) -> bool:
        return False

    async def send(self, db: AsyncSession, row: NotificationOutbox) -> Optional[str]:
        """Deliver ``row``; return the provider message id. Raise ProviderNotConfigured or DeliveryError."""
        raise ProviderNotConfigured(self.key)


class InAppProvider(DeliveryProvider):
    key = "in_app"

    def is_configured(self) -> bool:
        return True

    async def send(self, db: AsyncSession, row: NotificationOutbox) -> Optional[str]:
        if not templates.known(row.template_key):
            raise DeliveryError("UNKNOWN_TEMPLATE")
        # idempotent: the outbox key doubles as the notification key
        existing = await db.execute(select(Notification.id).where(Notification.idempotency_key == row.idempotency_key))
        found = existing.scalar_one_or_none()
        if found:
            return found
        ntype, title, body = templates.render(row.template_key, row.safe_payload or {})
        payload = row.safe_payload or {}
        notif = Notification(
            recipient_id=row.recipient_id,
            campus_id=row.campus_id,
            notification_type=ntype,
            reference_id=row.case_id or payload.get("reference_id"),
            reference_type="case" if row.case_id else payload.get("reference_type"),
            title=title,
            body=body,
            is_read=False,
            idempotency_key=row.idempotency_key,
            sent_at=utc_now(),
        )
        db.add(notif)
        await db.flush()
        return notif.id


class EmailProvider(DeliveryProvider):
    """Plain SMTP. Configure with DISHA_SMTP_HOST (+ PORT, USER, PASSWORD, FROM, STARTTLS)."""
    key = "email"

    def is_configured(self) -> bool:
        return bool(os.getenv("DISHA_SMTP_HOST") and os.getenv("DISHA_SMTP_FROM"))

    async def send(self, db: AsyncSession, row: NotificationOutbox) -> Optional[str]:
        if not self.is_configured():
            raise ProviderNotConfigured(self.key)
        if not templates.known(row.template_key):
            raise DeliveryError("UNKNOWN_TEMPLATE")
        user = (await db.execute(select(User).where(User.id == row.recipient_id))).scalar_one_or_none()
        if not user or not user.is_active:
            raise DeliveryError("RECIPIENT_UNAVAILABLE")
        _, title, body = templates.render(row.template_key, row.safe_payload or {})
        msg = EmailMessage()
        msg["From"] = os.environ["DISHA_SMTP_FROM"]
        msg["To"] = user.email
        msg["Subject"] = title
        msg.set_content(body)
        try:
            await asyncio.to_thread(self._smtp_send, msg)
        except (OSError, smtplib.SMTPException) as exc:
            logger.warning("SMTP delivery failed for outbox %s: %s", row.id, type(exc).__name__)
            raise DeliveryError("SMTP_ERROR")
        return msg.get("Message-ID") or row.id

    @staticmethod
    def _smtp_send(msg: EmailMessage) -> None:
        host = os.environ["DISHA_SMTP_HOST"]
        port = int(os.getenv("DISHA_SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if os.getenv("DISHA_SMTP_STARTTLS", "true").lower() in ("1", "true", "yes"):
                smtp.starttls()
            if os.getenv("DISHA_SMTP_USER"):
                smtp.login(os.environ["DISHA_SMTP_USER"], os.getenv("DISHA_SMTP_PASSWORD", ""))
            smtp.send_message(msg)


class SmsProvider(DeliveryProvider):
    """Interface only: no SMS vendor is integrated, so this is never configured."""
    key = "sms"


def default_registry() -> Dict[str, DeliveryProvider]:
    return {p.key: p for p in (InAppProvider(), EmailProvider(), SmsProvider())}
