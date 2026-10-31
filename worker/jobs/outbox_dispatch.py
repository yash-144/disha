"""Deliver pending notification outbox rows (blueprint 07 section 5).

In-app rows become ``disha_notifications``. Email needs SMTP settings; SMS has no provider yet. An
adapter that is not configured logs a warning and leaves its rows ``pending``: nothing is marked sent
unless it was actually delivered. Logic lives in ``app.modules.notifications.dispatch``.
"""
import logging

from ._db import session_factory

logger = logging.getLogger("disha-worker.outbox")


async def run_outbox_dispatch(factory=None, registry=None) -> dict:
    factory = factory or session_factory()
    from app.modules.notifications.dispatch import process_outbox_batch

    async with factory() as db:
        try:
            counts = await process_outbox_batch(db, registry=registry)
        except Exception:
            await db.rollback()
            logger.exception("Outbox dispatch failed")
            raise
    if any(counts.values()):
        logger.info("Outbox batch: %s", counts)
    return counts
