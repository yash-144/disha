import logging

logger = logging.getLogger("disha-worker.outbox")

async def run_outbox_dispatch():
    logger.info("Executing outbox dispatch job...")
