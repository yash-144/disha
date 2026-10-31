"""Outbox dispatcher (blueprint 07 section 5). Called by ``worker/jobs/outbox_dispatch.py``.

* unknown ``adapter_key`` -> ``dead_letter`` / ``UNKNOWN_ADAPTER`` (OUT-01)
* adapter not configured -> row stays ``pending``, never ``sent`` (OUT-02); the retry is deferred
* delivery error -> exponential backoff, ``dead_letter`` after the configured max attempts (OUT-07)
* every attempt is logged with the provider message id (OUT-05)
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.notifications.models import NotificationOutbox, OutboxDeliveryAttempt
from app.modules.notifications.providers import (
    DeliveryError,
    DeliveryProvider,
    ProviderNotConfigured,
    default_registry,
)
from app.shared.utils import utc_now

logger = logging.getLogger("disha.notifications.dispatch")

# how long an unconfigured adapter's rows wait before being looked at again
UNCONFIGURED_RECHECK = timedelta(minutes=15)


async def process_outbox_batch(
    db: AsyncSession,
    registry: Optional[Dict[str, DeliveryProvider]] = None,
    now: Optional[datetime] = None,
    batch_size: Optional[int] = None,
) -> Dict[str, int]:
    """Deliver one batch of due ``pending`` rows. Commits. Returns counters."""
    registry = registry if registry is not None else default_registry()
    now = now or utc_now()
    batch_size = batch_size or settings.DISHA_OUTBOX_BATCH_SIZE
    max_attempts = settings.DISHA_OUTBOX_MAX_ATTEMPTS
    base_backoff = settings.DISHA_OUTBOX_BASE_BACKOFF_SECONDS

    stmt = (
        select(NotificationOutbox)
        .where(NotificationOutbox.status == "pending", NotificationOutbox.next_attempt_at <= now)
        .order_by(NotificationOutbox.next_attempt_at)
        .limit(batch_size)
    )
    dialect = getattr(getattr(db, "bind", None), "dialect", None)
    if dialect is not None and dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)  # several workers never take the same row

    rows = list((await db.execute(stmt)).scalars().all())
    counts = {"sent": 0, "deferred": 0, "retry": 0, "dead_letter": 0}
    warned = set()

    for row in rows:
        provider = registry.get(row.adapter_key)
        if provider is None:
            row.status = "dead_letter"
            row.last_error_code = "UNKNOWN_ADAPTER"
            counts["dead_letter"] += 1
            continue
        if not provider.is_configured():
            if row.adapter_key not in warned:
                logger.warning(
                    "Notification adapter '%s' is not configured; leaving its outbox rows pending", row.adapter_key
                )
                warned.add(row.adapter_key)
            row.next_attempt_at = now + UNCONFIGURED_RECHECK
            counts["deferred"] += 1
            continue

        try:
            async with db.begin_nested():
                message_id = await provider.send(db, row)
        except ProviderNotConfigured:
            row.next_attempt_at = now + UNCONFIGURED_RECHECK
            counts["deferred"] += 1
            continue
        except DeliveryError as exc:
            _record_failure(db, row, exc.code, now, max_attempts, base_backoff, counts)
            continue
        except Exception:  # noqa: BLE001 - one bad row must not stop the batch
            logger.exception("Unexpected error delivering outbox row %s", row.id)
            _record_failure(db, row, "UNEXPECTED_ERROR", now, max_attempts, base_backoff, counts)
            continue

        row.attempts += 1
        row.status = "sent"
        row.sent_at = now
        row.last_error_code = None
        db.add(
            OutboxDeliveryAttempt(
                outbox_id=row.id, campus_id=row.campus_id, adapter_key=row.adapter_key,
                outcome="sent", provider_message_id=message_id, attempted_at=now,
            )
        )
        counts["sent"] += 1

    await db.commit()
    return counts


def _record_failure(db, row, code, now, max_attempts, base_backoff, counts) -> None:
    row.attempts += 1
    row.last_error_code = code
    db.add(
        OutboxDeliveryAttempt(
            outbox_id=row.id, campus_id=row.campus_id, adapter_key=row.adapter_key,
            outcome="failed", error_code=code, attempted_at=now,
        )
    )
    if row.attempts >= max_attempts or code in ("UNKNOWN_TEMPLATE", "RECIPIENT_UNAVAILABLE"):
        row.status = "dead_letter"
        counts["dead_letter"] += 1
    else:
        row.next_attempt_at = now + timedelta(seconds=base_backoff * 2 ** (row.attempts - 1))
        counts["retry"] += 1
