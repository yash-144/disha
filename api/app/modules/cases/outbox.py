"""Outbox dispatch with exponential backoff and a dead-letter state (OUT-01, OUT-02, OUT-07)."""
import logging
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.cases.models import OutboxItem
from app.shared.utils import utc_now

log = logging.getLogger("disha.outbox")
Adapter = Callable[[OutboxItem], Awaitable[None]]


async def in_app(item: OutboxItem) -> None:
    """The outbox row is the in-app notification (no separate notifications table yet)."""
    log.info("in_app %s -> %s", item.template_key, item.destination_ref)


DEFAULT_ADAPTERS: Dict[str, Adapter] = {"in_app": in_app}


async def dispatch_batch(db: AsyncSession, adapters: Optional[Dict[str, Adapter]] = None,
                         now: Optional[datetime] = None, batch_size: Optional[int] = None,
                         max_attempts: Optional[int] = None, base_backoff: Optional[int] = None) -> Dict[str, int]:
    """Send due rows. Failure k waits base * 2**(k-1) seconds; the max_attempts-th failure dead-letters.

    No adapters configured -> nothing is touched (rows stay pending, never falsely 'sent').
    """
    adapters = DEFAULT_ADAPTERS if adapters is None else adapters
    stats = {"sent": 0, "retry": 0, "dead_letter": 0}
    if not adapters:
        return stats
    now = now or utc_now()
    max_attempts = max_attempts or settings.DISHA_OUTBOX_MAX_ATTEMPTS
    base_backoff = base_backoff or settings.DISHA_OUTBOX_BASE_BACKOFF_SECONDS
    q = (select(OutboxItem).where(OutboxItem.status == "pending", OutboxItem.next_attempt_at <= now)
         .order_by(OutboxItem.created_at).limit(batch_size or settings.DISHA_OUTBOX_BATCH_SIZE)
         .with_for_update(skip_locked=True))
    for item in (await db.execute(q)).scalars():
        adapter = adapters.get(item.adapter_key)
        if adapter is None:
            item.status, item.last_error = "dead_letter", "UNKNOWN_ADAPTER"
            stats["dead_letter"] += 1
            continue
        item.attempts += 1
        try:
            await adapter(item)
            item.status, item.sent_at, item.last_error = "sent", now, None
            stats["sent"] += 1
        except Exception as exc:  # noqa: BLE001 - any adapter failure is retried
            item.last_error = f"{type(exc).__name__}: {exc}"[:200]
            if item.attempts >= max_attempts:
                item.status = "dead_letter"
                stats["dead_letter"] += 1
            else:
                item.next_attempt_at = now + timedelta(seconds=base_backoff * 2 ** (item.attempts - 1))
                stats["retry"] += 1
    await db.commit()
    return stats
