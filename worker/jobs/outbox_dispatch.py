import logging

from . import _db
from app.modules.cases.outbox import dispatch_batch

logger = logging.getLogger("disha-worker.outbox")


async def run_outbox_dispatch():
    """Send due outbox rows; retries back off exponentially, then dead-letter."""
    async with _db.session() as db:
        stats = await dispatch_batch(db)
    if any(stats.values()):
        logger.info("outbox: %s", stats)
    return stats
