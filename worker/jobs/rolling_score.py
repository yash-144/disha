"""Daily rolling-risk scoring of every in-session term that has ingested data (see api/app/modules/ml/jobs.py)."""
import logging

logger = logging.getLogger("disha-worker.rolling-score")


async def run_rolling_score():
    try:
        from app.core.config import settings
        from app.core.database import AsyncSessionLocal
        from app.modules.ml.jobs import run_scheduled_scoring
    except ImportError as exc:
        logger.warning("Rolling scoring skipped: %s", exc)
        return []
    if not settings.DISHA_ML_SCHEDULED_SCORING or AsyncSessionLocal is None:
        return []
    try:
        runs = await run_scheduled_scoring(AsyncSessionLocal)
    except Exception:  # noqa: BLE001
        logger.exception("Rolling scoring failed")
        return []
    logger.info("Rolling scoring: %d run(s) created", len(runs))
    return runs
