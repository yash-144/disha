import logging
from jobs.outbox_dispatch import run_outbox_dispatch
from jobs.deadline_escalation import run_deadline_escalation
from jobs.anchor_confirmation import run_anchor_confirmation
from jobs.retention_purge import run_retention_purge
from jobs.model_drift_report import run_model_drift_report

logger = logging.getLogger("disha-worker.scheduler")

class DummyScheduler:
    def __init__(self):
        self.jobs = [
            ("outbox_dispatch", run_outbox_dispatch, 10),
            ("deadline_escalation", run_deadline_escalation, 60),
            ("anchor_confirmation", run_anchor_confirmation, 300),
            ("retention_purge", run_retention_purge, 86400),
            ("model_drift_report", run_model_drift_report, 86400),
        ]
    def shutdown(self):
        logger.info("Scheduler shutdown.")

def init_scheduler():
    scheduler = DummyScheduler()
    logger.info(f"Registered {len(scheduler.jobs)} DISHA recurring worker jobs.")
    return scheduler
