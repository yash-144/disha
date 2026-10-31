"""Daily model drift report: PSI of each campus's latest scoring run against the training reference.

The per-run PSI is computed and persisted by the scoring service (`disha_ml_runs.data_drift`). This job compares the
latest run with the previous one per campus and logs a warning when a retrain is recommended. Aggregates only.
"""
import logging

logger = logging.getLogger("disha-worker.drift")


async def run_model_drift_report():
    try:
        from app.core.database import AsyncSessionLocal
        from app.modules.ml.jobs import drift_summaries
    except ImportError as exc:  # the API package (and its ml extras) must be on the worker's path
        logger.warning("Drift report skipped: %s", exc)
        return []
    if AsyncSessionLocal is None:
        logger.warning("Drift report skipped: database layer unavailable")
        return []
    try:
        reports = await drift_summaries(AsyncSessionLocal)
    except Exception:  # noqa: BLE001 - a failed report must not stop the scheduler
        logger.exception("Drift report failed")
        return []
    if not reports:
        logger.info("Drift report: no completed scoring runs yet")
    for r in reports:
        level = logger.warning if r["retrain_recommended"] else logger.info
        level("Drift campus=%s run=%s day=%s model=%s max_psi=%s (previous %s) retrain_recommended=%s shifted=%s",
              r["campus_id"], r["run_id"], r["as_of_day"], r["model_version"], r["max_psi"],
              r["previous_max_psi"], r["retrain_recommended"], r["shifted_features"])
    return reports
