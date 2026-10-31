import asyncio
import logging
from scheduler import init_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [DISHA Worker]: %(message)s")
logger = logging.getLogger("disha-worker")

async def main():
    logger.info("Initializing DISHA Background Worker...")
    scheduler = init_scheduler()
    logger.info("DISHA Background Worker running. Scheduled jobs active.")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping DISHA Background Worker...")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
