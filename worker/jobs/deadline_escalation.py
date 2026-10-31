"""Escalate overdue cases and follow-ups (blueprint 07 section 4). Logic: ``app.modules.cases.escalation``."""
import logging

from ._db import session_factory

logger = logging.getLogger("disha-worker.escalation")


async def run_deadline_escalation(factory=None):
    factory = factory or session_factory()
    from app.modules.cases.escalation import scan_and_escalate

    async with factory() as db:
        try:
            cases, followups = await scan_and_escalate(db)
        except Exception:
            await db.rollback()
            logger.exception("Deadline escalation failed")
            raise
    if cases or followups:
        logger.info("Escalated %d case(s) and %d follow-up(s)", cases, followups)
    return cases, followups
