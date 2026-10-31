import logging

logger = logging.getLogger("disha-worker.drift")

async def run_model_drift_report():
    logger.info("Executing ML model drift calculation...")
