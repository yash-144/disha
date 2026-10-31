import logging

from . import _db
from app.modules.cases.services import escalate_overdue

logger = logging.getLogger("disha-worker.escalation")


async def run_deadline_escalation():
    """Escalate cases and tasks past their deadline (case_event + outbox notification)."""
    async with _db.session() as db:
        stats = await escalate_overdue(db)
    if any(stats.values()):
        logger.info("escalated: %s", stats)
    return stats
