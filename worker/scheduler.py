import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from jobs.outbox_dispatch import run_outbox_dispatch
from jobs.deadline_escalation import run_deadline_escalation
from jobs.anchor_confirmation import run_anchor_confirmation
from jobs.retention_purge import run_retention_purge
from jobs.model_drift_report import run_model_drift_report
from jobs.rolling_score import run_rolling_score
from jobs.meko_sync import run_meko_weekly_outcomes

logger = logging.getLogger("disha-worker.scheduler")

JOBS = [  # (id, coroutine, interval seconds)
    ("outbox_dispatch", run_outbox_dispatch, 10),
    ("deadline_escalation", run_deadline_escalation, 60),
    ("anchor_confirmation", run_anchor_confirmation, 300),
    ("retention_purge", run_retention_purge, 86400),
    ("rolling_score", run_rolling_score, 86400),
    ("model_drift_report", run_model_drift_report, 86400),
    ("meko_weekly_outcomes", run_meko_weekly_outcomes, 604800),
]


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    for job_id, fn, seconds in JOBS:  # one run at a time per job; missed runs collapse into one
        scheduler.add_job(fn, "interval", seconds=seconds, id=job_id, max_instances=1, coalesce=True)
    return scheduler


def init_scheduler() -> AsyncIOScheduler:
    """Start the scheduler; call from inside a running event loop."""
    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Started %d DISHA recurring worker jobs.", len(JOBS))
    return scheduler
