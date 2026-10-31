import logging

logger = logging.getLogger("disha-worker.purge")

async def run_retention_purge():
    logger.info("Executing data retention purge policy...")
